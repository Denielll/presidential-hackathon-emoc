
from flask import Flask, jsonify, Blueprint,request
import pandas as pd
import json
from sqlalchemy import create_engine
# from flask_cors import CORS
import pymongo
import simplejson
import urllib
import config


app = Flask(__name__)
# CORS(app)


uri = 'mongodb+srv://' + config.credentials['username'] + ':' + config.credentials['password'] + '@' + config.credentials['host'] 
client = pymongo.MongoClient(uri)
db = client[config.credentials['database']]






@app.route('/KAMERA/')
def get_kamera():

	ambulance_latlng = request.args.get('latlng', default = 1, type = str)
	timestamp = request.args.get('timestamp', default = 1, type = str)

	if not ambulance_latlng:
		return(bad_request_kamera())

	else:
		df = pd.DataFrame(list(db["kamera"].find({"updated_timestamp":timestamp})))


		g = []
		orig_coord = ambulance_latlng
		for i in list(df["hospital_latlng"]):
			dest_coord = i
			url = "http://maps.googleapis.com/maps/api/distancematrix/json?origins={0}&destinations={1}&mode=driving&language=en-EN&sensor=false".format(str(orig_coord),str(dest_coord))
			result= simplejson.load(urllib.request.urlopen(url))
			driving_time = result['rows'][0]['elements'][0]['duration']['value']
			g.append(driving_time)

		df["traveling_time"] = g
		hospital_nearby = df.sort_values("traveling_time" , ascending=True )[:10]
		del hospital_nearby["_id"]

		response = jsonify(dict(result=hospital_nearby.to_json( orient="records" )))
		response.status_code = 200


		return response













@app.route('/ePCR/', methods=["POST"])
def post_epcr():
	try:
		test_json = request.get_json()
	except Exception as e:
		raise e


	if not "ePCR_id"  or not "device_id" in  list(test_json.keys()):
		return bad_request_epcr()

	#   {ePCR_id} exists
	elif  list(db["epcr"].find({"ePCR_id":test_json["ePCR_id"]})):
		return forbidden_epcr()

	else:
		# 塞入 DB
		print("hihihihi")
		db["epcr"].insert_one(test_json)


		message = {
			'result': "success",
		}
		resp = jsonify(message)
		resp.status_code = 200
		return resp






@app.route('/ePCR/<epcr_id>', methods=["GET"])
def get_epcr(epcr_id):


	query = {"ePCR_id":epcr_id}
	projection = {'device_id': 0 , "_id":0}
	result_ = list(db["epcr"].find(query, projection))

	response = jsonify(dict(result=result_))
	response.status_code = 200



	return response




@app.route('/ePCR/<epcr_id>', methods=["PUT"])
def put_epcr(epcr_id):

	try:
		test_json = request.get_json()
	except Exception as e:
		raise e
	
	# ePCR_id does not exist
	if not list(db["epcr"].find({"ePCR_id":epcr_id})):
		return not_found_epcr()

	else:
		db["epcr"].update_one({'ePCR_id':epcr_id }, {"$set":test_json},upsert=False)
		message = {
			'result': "success",
		}
		resp = jsonify(message)
		resp.status_code = 200
		return resp




@app.route('/ePCR/<epcr_id>', methods=["DELETE"])
def delete_epcr(epcr_id):

	# ePCR_id does not exist
	if not list(db["epcr"].find({"ePCR_id":epcr_id})):
		return not_found_epcr()
	else:
		db["epcr"].remove({"ePCR_id":epcr_id})
		message = {
			'result': "success",
		}
		resp = jsonify(message)
		resp.status_code = 200
		return resp








   
@app.errorhandler(400)
def bad_request_kamera(error=None):
	message = {
			'status': 400,
			'message': 'Bad Request ! Please specify latlng'  
	}
	resp = jsonify(message)
	resp.status_code = 400

	return resp



@app.errorhandler(400)
def bad_request_epcr(error=None):
	message = {
			'status': 400,
			'message': 'Bad Request ! Please specify ePCR_id and device_id'  
	}
	resp = jsonify(message)
	resp.status_code = 400

	return resp


@app.errorhandler(403)
def forbidden_epcr(error=None):
	message = {
			'status': 403,
			'message': 'forbidden ! ePCR_id already exists'  
	}
	resp = jsonify(message)
	resp.status_code = 403

	return resp


@app.errorhandler(404)
def not_found_epcr(error=None):
	message = {
			'status': 404,
			'message': '404 not found ! ePCR_id does not exist'  
	}
	resp = jsonify(message)
	resp.status_code = 404

	return resp






if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)






