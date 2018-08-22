import boto3
import re
import certifi
from datetime import datetime
from elasticsearch import Elasticsearch
from elasticsearch import helpers
from aws_requests_auth.boto_utils import BotoAWSRequestsAuth
from elasticsearch import Elasticsearch, RequestsHttpConnection


def lambda_handler(event, context):
	ELB_KEYS = ["timestamp", "elb", "client_ip", "client_port", "backend_ip", "backend_port", "request_processing_time", "backend_processing_time", "response_processing_time", "elb_status_code", "backend_status_code", "received_bytes", "sent_bytes", "request_method", "request_url", "request_version", "user_agent"]
	ELB_REGEX = '^(.[^ ]+) (.[^ ]+) (.[^ ]+):(\\d+) (.[^ ]+):(\\d+) (.[^ ]+) (.[^ ]+) (.[^ ]+) (.[^ ]+) (.[^ ]+) (\\d+) (\\d+) \"(\\w+) (.[^ ]+) (.[^ ]+)\" \"(.+)\"'
	ELB_REGEX_2 = '^(.[^ ]+) (.[^ ]+) (.[^ ]+):(\\d+) (-)( )(.[^ ]+) (.[^ ]+) (.[^ ]+) (.[^ ]+) (\\d+) (\\d+) (\\d+) \"(\\w+) (.[^ ]+) (.[^ ]+)\" \"(.+)\"'
	R = re.compile(ELB_REGEX)
	R2 = re.compile(ELB_REGEX_2)

	ES_HOST = "elb_endpoint"
	INDEX_PREFIX = ""
	BUCKET_NAME = "bucket_name"

	auth = BotoAWSRequestsAuth(aws_host=ES_HOST,
						   aws_region='us-east-1',
						   aws_service='es')
	es = Elasticsearch(host=ES_HOST, port=443, use_ssl=True, ca_certs=certifi.where(), connection_class=RequestsHttpConnection, http_auth=auth)
	actions = []
	elb_name = ""
	error=0

	s3 = boto3.client("s3")
	if event:
		print("Event:", event)
		file_obj = event["Records"][0]
		filename = str(file_obj['s3']['object']['key'])
		print("Filename: ", filename)
		fileObj = s3.get_object(Bucket = BUCKET_NAME, Key=filename)
		file_content = fileObj["Body"].read().decode('utf-8')
		#print(file_content)
		for line in file_content.strip().split("\n"):
			match = R.match(line)
			if not match:
				match = R2.match(line)
				if not match:
					error=error+1
					print("Error: ",line)
					continue

			values = match.groups(0)
			if not elb_name:
				elb_name = ("%s_doc") %(values[1])
				INDEX_PREFIX = ("%s-%s-w%s") %(values[1], datetime.now().isocalendar()[0], datetime.now().isocalendar()[1])
				print values[1]
			doc = dict(zip(ELB_KEYS, values))
			#print doc

			actions.append({"_index": INDEX_PREFIX, "_type": elb_name, "_source": doc})

			if len(actions) > 300:
				helpers.bulk(es, actions)
				print("bulk elastic")
				actions = []

		if len(actions) > 0:
			print("end bulk elastic")
			helpers.bulk(es, actions)
		print("erros:", error)
