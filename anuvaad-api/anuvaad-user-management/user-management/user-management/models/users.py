from utilities import MODULE_CONTEXT
from db import get_db
from anuvaad_auditor.loghandler import log_info, log_exception

class UserManagementModel(object):

    @staticmethod
    def create_users(userID,name,userName,password,email,phoneNo,roleCode,roleDesc):
        try:
            collections = get_db()['sample']
            user         = collections.insert([{'userID': userID},{'name':name},{'userName': userName},{'password': password},{'email': email},{'phoneNo': phoneNo},{'roles':[{'roleCode':roleCode},{'roleDesc':roleDesc}]}])
            return user
        except Exception as e:
            log_exception("db connection exception ",  MODULE_CONTEXT, e)
            return None
        
    # @staticmethod
    # def update_users_by_u_id(user_id, s_id):
    #     try:
    #         collections = get_db()['file_content']
    #         docs        = collections.aggregate([
    #                 { '$match': {'data.tokenized_sentences.s_id' : s_id } },
    #                 { '$project': {
    #                     'tokenized_sentences': {
    #                         '$filter': {
    #                             'input': '$data.tokenized_sentences',
    #                             'as': 'ts',
    #                             'cond': { '$eq': ['$$ts.s_id', s_id] }
    #                             }
    #                         }
    #                     }
    #                 }
    #             ])
            
    #         for doc in docs:
    #             sentence = doc['tokenized_sentences'][0]
    #             if 's0_tgt' not in list(sentence.keys()):
    #                 sentence['s0_tgt'] = sentence['tgt']
    #             if 's0_src' not in list(sentence.keys()):
    #                 sentence['s0_src'] = sentence['src']
    #             return sentence

    #         return None
    #     except expression as identifier:
    #         log_exception("db connection exception ",  MODULE_CONTEXT, e)
    #         return None

    # @staticmethod
    # def get_user_by_keys(user_id, sentence):
    #     SENTENCE_KEYS   = ['n_id', 'pred_score', 's_id', 'src', 'tgt']
    #     try:
    #         collections     = get_db()['file_content']

    #         results         = collections.update({'$and': [{'created_by': user_id}, { 'data.tokenized_sentences': {'$elemMatch': {'s_id': {'$eq': sentence['s_id']}}}}]},
    #                                             {
    #                                                 '$set':
    #                                                 {
    #                                                     "data.tokenized_sentences.$.n_id" : sentence['n_id'],
    #                                                     "data.tokenized_sentences.$.src"  : sentence['src'],
    #                                                     "data.tokenized_sentences.$.tgt"  : sentence['tgt'],
    #                                                 }
    #                                             }, upsert=False)

    #         if 'writeError' in list(results.keys()):
    #             return False
    #         return True        
    #     except expression as identifier:
    #         log_exception("db connection exception ",  MODULE_CONTEXT, e)
    #         return False
