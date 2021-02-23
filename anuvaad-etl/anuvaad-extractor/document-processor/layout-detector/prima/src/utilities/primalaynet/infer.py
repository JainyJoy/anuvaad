import layoutparser as lp
import cv2
from anuvaad_auditor.loghandler import log_info
from anuvaad_auditor.loghandler import log_exception
import src.utilities.app_context as app_context
import uuid
from config import PRIMA_SCORE_THRESH_TEST, LAYOUT_CONFIG_PATH,LAYOUT_MODEL_PATH,LAYOUT_CELL_CONFIG_PATH,LAYOUT_CELL_MODEL_PATH,PRIMA_CELL_SCORE_THRESH_TEST
from collections import namedtuple
Rectangle = namedtuple('Rectangle', 'xmin ymin xmax ymax')
import sys, random, torch, glob, torchvision
import os
import numpy as np
import copy
from shapely.geometry import Polygon
from src.utilities.remove_water_mark import clean_image

#device = torch.device("cpu")
os.environ["CUDA_VISIBLE_DEVICES"] = ""

seed = 1234
random.seed(seed)
torch.manual_seed(seed)
#if torch.cuda.is_available():
#	torch.cuda.device(0)
# torch.cuda.manual_seed_all(seed)
# torch.backends.cudnn.deterministic = True
# torch.backends.cudnn.benchmark = False
#
#model_primalaynet = lp.Detectron2LayoutModel('lp://PrimaLayout/mask_rcnn_R_50_FPN_3x/config',label_map = {1:"TextRegion", 2:"ImageRegion", 3:"TableRegion", 4:"MathsRegion", 5:"SeparatorRegion", 6:"OtherRegion"},extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", PRIMA_SCORE_THRESH_TEST])#,"MODEL.ROI_HEADS.NMS_THRESH_TEST", 0.2])
# model_primalaynet = lp.Detectron2LayoutModel(
model_primatablenet = lp.Detectron2LayoutModel(LAYOUT_CELL_CONFIG_PATH,model_path = LAYOUT_CELL_MODEL_PATH,label_map = {0:"CellRegion"},extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", PRIMA_CELL_SCORE_THRESH_TEST])

model_primalaynet = lp.Detectron2LayoutModel(LAYOUT_CONFIG_PATH,model_path = LAYOUT_MODEL_PATH,label_map = {0:"FooterRegion", 1:"TextRegion", 2:"ImageRegion", 3:"TableRegion", 4:"HeaderRegion", 5:"OtherRegion"},extra_config=["MODEL.ROI_HEADS.SCORE_THRESH_TEST", PRIMA_SCORE_THRESH_TEST])

class MapKeys:
    def __init__(self):
        self.left    =  None
        self.right   =  None
        self.top     =  None
        self.bottom  =  None

    def get_left(self,box):
        left = int(box['boundingBox']['vertices'][0]['x'])
        return left

    def get_right(self,box):
        right = int(box['boundingBox']['vertices'][1]['x'])
        return right

    def get_top(self,box):
        top = int(box['boundingBox']['vertices'][0]['y'])
        return top

    def get_bottom(self,box):
        bottom = int(box['boundingBox']['vertices'][3]['y'])
        return bottom
    def get_height(self,box):
        height = int(abs(self.get_top(box) - self.get_bottom(box)))
        return height
    def get_width(self,box):
        width =  int(abs(self.get_left(box) - self.get_right(box)))
        return width

keys = MapKeys()

class PRIMA(object): 
	def area(self,a, b):  # returns None if rectangles don't intersect
		dx = min(a.xmax, b.xmax) - max(a.xmin, b.xmin)
		dy = min(a.ymax, b.ymax) - max(a.ymin, b.ymin)
		if (dx>=0) and (dy>=0):
			return dx*dy
	def prima_region(self, layout):
		bbox = []; tag =[]
		for idx, ele in enumerate(layout):
			if ele.type is not 'TableRegion':
				bbox.append(list(ele.coordinates))
				tag.append(ele.type)
		return bbox,tag

	def craft_refinement(self, boxes_final, coords, layout_class):
		if len(boxes_final) != 0:
			for box in boxes_final:
				vertical_min_dis = sys.maxsize; horizon_min_dis  = sys.maxsize
				ver_coord_update = None;  hor_coord_update = None
				hor_index = None;  ver_inex  = None
				for idx,coord in enumerate(coords):
					top_dis      = abs(coord[1]-box[1]); left_dis   = abs(coord[0]-box[2])
					bottom_dis   = abs(coord[1]-box[3]); right_dis  = abs(coord[2]-box[2])
					top_dis1     = abs(coord[3]-box[1]); left_dis1  = abs(coord[0]-box[0])
					bottom_dis1  = abs(coord[3]-box[3]); right_dis1 = abs(coord[2]-box[0])
					vertical_dis = min(top_dis,bottom_dis,top_dis1,bottom_dis1)
					horizon_dis  = min(left_dis,right_dis,left_dis1,right_dis1)
					if (vertical_min_dis > vertical_dis and abs(box[0]-coord[0]) < 100):
						vertical_min_dis = vertical_dis
						ver_coord_update = coord
						ver_index        = idx
					if horizon_min_dis>horizon_dis:
						horizon_min_dis  = horizon_dis
						hor_coord_update = coord
						hor_index        = idx
				
				if abs(vertical_min_dis)<150 :
					coords[ver_index][0] = int(min(ver_coord_update[0],box[0])); coords[ver_index][1] = int(min(ver_coord_update[1],box[1]))
					coords[ver_index][2] = int(max(ver_coord_update[2],box[2])); coords[ver_index][3] = int(max(ver_coord_update[3],box[3]))
				#elif abs(horizon_min_dis)<10:
					
					#coords[hor_index][0] = int(min(hor_coord_update[0],box[0])); coords[hor_index][1] = int(min(hor_coord_update[1],box[1]))
					#coords[hor_index][2] = int(max(hor_coord_update[2],box[2])); coords[hor_index][3] = int(max(hor_coord_update[3],box[3]))
				else:
					layout_class.append('TextRegion')
					coords.append(box)

		return coords, layout_class

	def prima_craft_refinement(self, coords, boxes, tag_final):
		org_coord     = coords
		org_coord2    = coords
		boxes_final   = []

		for idx1, coord1 in enumerate(boxes):
			min_area = 0; count=0
			index=idx1; check =False
			for idx2, coord2 in enumerate(org_coord):
				ra = Rectangle(coord1[0],coord1[1],coord1[2],coord1[3])
				rb = Rectangle(int(coord2[0]),int(coord2[1]), int(coord2[2]),int(coord2[3]))
				ar = self.area(ra, rb)
				
				if ar!=None and min_area<ar:
					min_area =ar;  index= idx2;  check =True
				if ar==None:
					count=count+1
			if check ==True:
				org_coord2[index][0] = int(min(coord1[0],org_coord2[index][0])); org_coord2[index][1] = int(min(coord1[1],org_coord2[index][1]))
				org_coord2[index][2] = int(max(coord1[2],org_coord2[index][2])); org_coord2[index][3] = int(max(coord1[3],org_coord2[index][3]))
				
			if count == len(org_coord):
				boxes_final.append(coord1)
				tag_final.append("TextRegion")


		coords, layout_class  = self.craft_refinement(boxes_final, coords, tag_final)
		
		
		return coords, layout_class
	
	def get_polygon(self, region):
		points = []
		vertices = region['vertices']
		for point in vertices:
			points.append((point['x'], point['y']))
		poly = Polygon(points)
		return poly

	def class_mapping(self, class_name):
		if class_name == "TextRegion":
			class_name = "TEXT"
		if class_name == "TableRegion":
			class_name = "TABLE"
		if class_name == "ImageRegion":
			class_name = "IMAGE"
		if class_name == "MathsRegion":
			class_name = "MATH"
		if class_name == "HeaderRegion":
			class_name = "HEADER"
		if class_name == "OtherRegion":
			class_name = "OTHER"
		if class_name == "FooterRegion":
			class_name = "FOOTER"
		if class_name == "SeparatorRegion":
			class_name = "SEPARATOR"
		if class_name == "CellRegion":
			class_name = "CELL"

		return class_name

	def update_box_format(self,coords,tags):
		final_coord =[]
		for idx,coord in enumerate(coords):
			temp_dict = {}; vert=[]
			temp_dict['identifier'] = str(uuid.uuid4())
			vert.append({'x':coord[0],'y':coord[1]})
			vert.append({'x':coord[2],'y':coord[1]})
			vert.append({'x':coord[2],'y':coord[3]})
			vert.append({'x':coord[0],'y':coord[3]})
			temp_dict['boundingBox']={}
			temp_dict['boundingBox']["vertices"] = vert

			temp_dict['class']      = self.class_mapping(tags[idx])
			final_coord.append(temp_dict)
		return final_coord
	def update_coord(self,reg1,reg2,clss):
        #try:
		box1_top = keys.get_top(reg1); box1_bottom = keys.get_bottom(reg1)
		box1_left = keys.get_left(reg1); box1_right = keys.get_right(reg1)
		box2_top = keys.get_top(reg2); box2_bottom = keys.get_bottom(reg2)
		box2_left = keys.get_left(reg2); box2_right = keys.get_right(reg2)


		reg1["boundingBox"]["vertices"][0]['x']= min(box1_left,box2_left)
		reg1["boundingBox"]["vertices"][0]['y']= min(box1_top,box2_top)
		reg1["boundingBox"]["vertices"][1]['x']= max(box1_right,box2_right)
		reg1["boundingBox"]["vertices"][1]['y']= min(box1_top,box2_top)
		reg1["boundingBox"]["vertices"][2]['x']= max(box1_right,box2_right)
		reg1["boundingBox"]["vertices"][2]['y']= max(box1_bottom,box2_bottom)
		reg1["boundingBox"]["vertices"][3]['x']= min(box1_left,box2_left)
		reg1["boundingBox"]["vertices"][3]['y']= max(box1_bottom,box2_bottom)
		#reg1['class'] = 'TEXT'
		# except:
		#     pass

		return reg1

	def is_connected(self,region1, region2,height,width):
        
		region_poly = self.get_polygon(region2['boundingBox'])
		base_poly = self.get_polygon(region1['boundingBox'])
		area = base_poly.intersection(region_poly).area
		area1 = base_poly.area
		area2 = region_poly.area
		tag1 = region1['class']
		tag2 = region2['class']
		score1 = region1['score']
		score2 = region2['score']
		y1 = keys.get_top(region1); y2 = keys.get_top(region2)
		if tag1=="CELL" or tag2=="CELL" or tag1=="TABLE" or tag2=="TABLE":
			return None, False
		if (area>0 and area1<area2 and area1/area2>0.2 and score1>score2) or (area>0 and area1>area2 and area2/area1>0.2 and  score1>score2):
				return tag1, True
		elif (area>0 and area1<area2 and area1/area2>0.2 and score1<score2) or (area>0 and area1>area2 and area2/area1>0.2 and  score1<score2):
				return tag2, True
		else:
			return None, False
		# if (area>0 and tag1=='OTHER') or (area>0 and tag2=='OTHER'):
		# 	if tag1!='OTHER':
		# 		return tag1, True
		# 	else:
		# 		return tag2, True
		# elif (area>0 and tag1=='FOOTER' and y1<height*0.75) or (area>0 and tag2=='FOOTER' and y2<height*0.75):
		# 	if tag1!='FOOTER':
		# 		return tag1, True
		# 	else:
		# 		return tag2, True	
		# elif (area>0 and tag1=='FOOTER' and y1>=height*0.75) or (area>0 and tag2=='FOOTER' and y2>height*0.75):
		# 	if (tag1=='FOOTER' and area1/area2>0.8 ) or (area2/area1>0.8 and tag2=='FOOTER'):
		# 		return 'FOOTER', True
		# 	elif tag1!='FOOTER':
		# 		return tag1, True
		# 	else:
		# 		return tag2, True
		# elif (area>0 and tag1=='HEADER'  and y1>height*0.30) or (area>0 and tag2=='HEADER' and y2>height*0.30):
		# 	if tag1!='HEADER':
		# 		return tag1, True
		# 	else:
		# 		return tag2, True
		# elif (area>0 and tag1=='HEADER' and y1<height*0.30) or (area>0 and tag2=='HEADER'  and y2<height*0.30):
		# 	if (tag1=='HEADER'and area1/area2>0.8) or (tag2=='HEADER' and area2/area1>0.8):
		# 		return 'HEADER', True
		# 	elif tag1!='HEADER':
		# 		return tag1, True
		# 	else:
		# 		return tag2, True
		# elif (area>0 and tag1==tag2):
		# 	return tag1, True
		# else:
		# 	if (area>0 and area1<area2 and area1/area2>0.8) or (area>0 and area1>area2 and area2/area1>0.8):
		# 		return tag1, True
		# 	else:
		# 		return None, False
        #check = self.check_region_unification(region1,region2,avg_height, avg_ver_dist, avg_width,avg_word_sepc)
        #return  area>0 and 

	def merge_remove_overlap(self,text_regions,height,width):
		region_updated = []
		flag =False
		while len(text_regions)>0:
			check = False
			region_temp= text_regions[1:]
			for idx2,region2 in enumerate(region_temp):
				clss, cond = self.is_connected(text_regions[0], region2,height,width)
				if cond:
					region1 = self.update_coord(text_regions[0],region2,clss)
					text_regions[0] = copy.deepcopy(region1)
					check =True ;  flag = True
					del text_regions[idx2+1]
					break    
			if check == False:
				region_updated.append(copy.deepcopy(text_regions[0]))
				del text_regions[0]
		return region_updated, flag

	def predict_primanet(self,image,craft_coords):
		try:
			#print(image,"iiiiiiiiiiiiiiiiiiiiiiiiii")
			#image   = cv2.imread("/home/naresh/anuvaad/anuvaad-etl/anuvaad-extractor/document-processor/layout-detector/prima/"+image)
			image   = cv2.imread(image)
			height, width, channels = image.shape
			#image = cv2.imread(image)
			#image   = clean_image(image)

			#image   = image[..., ::-1]
			layout   = model_primalaynet.detect(image)
			bbox,tag = self.prima_region(layout)
			############### craft refinement logic 
			#bbox, tag = self.prima_craft_refinement(bbox,craft_coords,tag)
			layouts  = self.update_box_format(bbox,tag)
			flag=True
			while flag==True:
				layouts, flag = self.merge_remove_overlap(layouts,height,width)
			

			return layouts
		except Exception as e:
			log_exception("Error occured during prima layout detection ",  app_context.application_context, e)
			return None


prima = PRIMA()
def cell_layout(table_regions,page_path):
	try:
		#print(image,"iiiiiiiiiiiiiiiiiiiiiiiiii")
		#image   = cv2.imread("/home/naresh/anuvaad/anuvaad-etl/anuvaad-extractor/document-processor/layout-detector/prima/"+image)
		image   = cv2.imread(page_path)
		height, width, channels = image.shape
		final_layouts=[]
		for region in table_regions:
			region = region['boundingBox']['vertices']
			bbox = [[region[0]['x'],region[0]['y'],region[2]['x'],region[2]['y']]]
			tab_layouts  = prima.update_box_format(bbox,['TableRegion'])[0]
			blank_image = np.zeros(image.shape, dtype=np.uint8)
			blank_image[:,0:image.shape[1]//2] = (255,255,255)      # (B, G, R)
			blank_image[:,image.shape[1]//2:image.shape[1]] = (255,255,255)
			ymin = region[0]['y'] ; ymax = region[2]['y'] ; xmin = region[0]['x']; xmax = region[2]['x']
			crop_img = image[ymin:ymax,xmin:xmax,:]
			blank_image[ymin:ymax,xmin:xmax] = crop_img
			layout   = model_primatablenet.detect(blank_image)
			bbox,tag = prima.prima_region(layout)
			layouts  = prima.update_box_format(bbox,tag)
			tab_layouts['children']=layouts
			final_layouts.append(tab_layouts)

		return final_layouts
	except Exception as e:
		log_exception("Error occured during cell layout detection",  app_context.application_context, e)
		return None