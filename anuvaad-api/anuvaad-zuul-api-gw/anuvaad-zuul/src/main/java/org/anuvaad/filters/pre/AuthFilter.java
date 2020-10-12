package org.anuvaad.filters.pre;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.netflix.zuul.ZuulFilter;
import com.netflix.zuul.context.RequestContext;
import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpStatus;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestTemplate;

import java.io.IOException;
import java.util.HashSet;

import static org.anuvaad.constants.RequestContextConstants.*;

/**
 * 2nd filter to execute in the request flow.
 * Checks if the auth token is available, throws exception otherwise.
 * for the given auth token checks if there's a valid user in the sysTem, throws exception otherwise.
 * Performs authentication level checks on the request.
 *
 */
@Component
public class AuthFilter extends ZuulFilter {

    @Value("#{'${anuvaad.open-endpoints-whitelist}'.split(',')}")
    private HashSet<String> openEndpointsWhitelist;

    @Value("${anuvaad.auth-service-host}")
    private String authServiceHost;

    @Value("${anuvaad.auth-service-host}")
    private String authUri;

    @Autowired
    private RestTemplate restTemplate;

    private final Logger logger = LoggerFactory.getLogger(this.getClass());

    private static final String AUTH_TOKEN_RETRIEVE_FAILURE_MESSAGE = "Retrieving of auth token failed";
    private static final String OPEN_ENDPOINT_MESSAGE = "Routing to an open endpoint: {}";
    private static final String AUTH_TOKEN_HEADER_NAME = "auth-token";
    private static final String ROUTING_TO_PROTECTED_ENDPOINT_RESTRICTED_MESSAGE = "Routing to protected endpoint {} restricted - No auth token";
    private static final String UNAUTHORIZED_USER_MESSAGE = "You are not authorized to access this resource";
    private static final String RETRIEVING_USER_FAILED_MESSAGE = "Retrieving user failed";
    private static final String PROCEED_ROUTING_MESSAGE = "Routing to protected endpoint: {} - auth provided";

    @Autowired
    private ObjectMapper objectMapper;

    @Override
    public String filterType() {
        return "pre";
    }

    @Override
    public int filterOrder() {
        return 1;
    } // Second filter

    @Override
    public boolean shouldFilter() {
        return true;
    }

    @Override
    public Object run() {
        String authToken;
        RequestContext ctx = RequestContext.getCurrentContext()
        if (openEndpointsWhitelist.contains(getRequestURI())) {
            setShouldDoAuth(false);
            logger.info(OPEN_ENDPOINT_MESSAGE, getRequestURI());
            return null;
        }
        try {
            authToken = getAuthTokenFromRequestHeader();
        } catch (IOException e) {
            logger.error(AUTH_TOKEN_RETRIEVE_FAILURE_MESSAGE, e);
            ExceptionUtils.RaiseException(e);
            return null;
        }
        ctx.set(AUTH_TOKEN_KEY, authToken);
        if (authToken == null) {
            logger.info(ROUTING_TO_PROTECTED_ENDPOINT_RESTRICTED_MESSAGE, getRequestURI());
            ExceptionUtils.raiseCustomException(HttpStatus.UNAUTHORIZED, UNAUTHORIZED_USER_MESSAGE);
            return null;
        } else {
            User user = verifyAuthenticity(ctx, authToken);
            if (null == user)
                ExceptionUtils.raiseCustomException(HttpStatus.INTERNAL_SERVER_ERROR, "User authentication service is down");
            else
                logger.info(PROCEED_ROUTING_MESSAGE, getRequestURI());
                setShouldDoAuth(true);
        }
        return null;
    }

    /**
     * Verifies if the authToken belongs to a valid user in the system.
     * @param ctx
     * @param authToken
     * @return
     */
    public User verifyAuthenticity(RequestContext ctx, String authToken) {
        try {
            User user = getUser(authToken, ctx);
            if (null != user)
                ctx.set(USER_INFO_KEY, user);
            return user;
        } catch (Exception ex) {
            logger.error(RETRIEVING_USER_FAILED_MESSAGE, ex);
            return null;
        }
    }

    /**
     * Fetches user from the UMS via API.
     * @param authToken
     * @param ctx
     * @return
     */
    private User getUser(String authToken, RequestContext ctx) {
        String authURL = String.format("%s%s%s", authServiceHost, authUri, authToken);
        final HttpHeaders headers = new HttpHeaders();
        headers.add(CORRELATION_ID_HEADER_NAME, (String) ctx.get(CORRELATION_ID_KEY));
        final HttpEntity<Object> httpEntity = new HttpEntity<>(null, headers);
        return restTemplate.postForObject(authURL, httpEntity, User.class);
    }

    /**
     * Fetches URI from the request
     * @return
     */
    private String getRequestURI() {
        RequestContext ctx = RequestContext.getCurrentContext();
        return ctx.getRequest().getRequestURI();
    }

    /**
     * Sets context auth prop.
     * @param enableAuth
     */
    private void setShouldDoAuth(boolean enableAuth) {
        RequestContext ctx = RequestContext.getCurrentContext();
        ctx.set(AUTH_BOOLEAN_FLAG_NAME, enableAuth);
    }

    /**
     * Fetches auth token from the request header.
     * @return
     */
    private String getAuthTokenFromRequestHeader() {
        RequestContext ctx = RequestContext.getCurrentContext();
        return ctx.getRequest().getHeader(AUTH_TOKEN_HEADER_NAME);
    }

}

