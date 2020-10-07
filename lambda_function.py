import boto3
import os
import gzip
import json
from botocore.exceptions import MissingParametersError
from datetime import datetime
from elasticsearch import helpers
import elasticsearch
import shlex


def lambda_handler(event, context):
    print("type of message",type(event['Records'][0]['Sns']['Message']))
    message = event['Records'][0]['Sns']['Message']
    if isinstance( message,str):
        tmp_message = json.loads(message)
        s3_message = tmp_message['Records'][0]['s3']
    else:
        s3_message = event['Records'][0]['Sns']['Message']['Records'][0]['s3']
    ## find the latest elb log fields here:https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-log-entry-format
    ELB_FIELD = ["elb.type",
                "elb.time",
                "elb.name",
                "elb.client_ip",
                "elb.target_ip",
                "elb.request_processing_time",
                "elb.target_processing_time",
                "elb.response_processing_time",
                "elb.elb_status_code",
                "elb.target_status_code",
                "elb.received_bytes",
                "elb.sent_bytes",
                "elb.request",
                "elb.user_agent",
                "elb.ssl_cipher",
                "elb.ssl_protocol",
                "elb.target_group_arn",
                "elb.trace_id",
                "elb.domain_name",
                "elb.chosen_cert_arn",
                "elb.matched_rule_priority",
                "elb.request_creation_time",
                "elb.actions_executed",
                "elb.redirect_url",
                "elb.error_reason",
                "elb.target_port_list",
                "elb.target_status_code_list",
                "elb.classification",
                "elb.classification_reason"
                ]
    ES_HOST = os.environ['ELASTIC_ENDPOINT']
    ES_REGION = os.environ['ES_REGION']
    INDEX_PREFIX = "aws.elb"
    #print(ES_HOST)
    #print(INDEX_PREFIX)
    today=datetime.utcnow().date()
    INDEX_PREFIX = INDEX_PREFIX + "-" + today.strftime("%Y-%m") 
    es = elasticsearch.Elasticsearch(ES_HOST, verify_certs=True, timeout = 60)
    try:
        es.indices.create(index=INDEX_PREFIX, ignore=400,timeout = 30)
        print("index created",INDEX_PREFIX)
    except elasticsearch.ConnectionError as  e:
        print("create index failed",e)
    except Exception as e:
        print("error:",e)


    actions = []
    s3 = boto3.resource("s3")

    if s3_message:
        filename = s3_message['object']['key']
        bucketname = s3_message['bucket']['name']
        file_obj = s3.Object(bucketname, filename)
        #print("Filename: ", filename, "\n", "bucket:", bucketname)
        with gzip.GzipFile(fileobj=file_obj.get()["Body"]) as gzipfile:
            file_content = gzipfile.read()
        file_content = file_content.decode('utf-8')
        #print(file_content)
        for line in file_content.strip().split("\n"):
            #print("----------------------")
            #print("orogin line:")
            new_line = shlex.split(line)
            #print(ELB_FIELD)
            #print(new_line)
            doc = dict(zip(ELB_FIELD, new_line))
            doc["elb.client_ip"] = doc["elb.client_ip"].split(':')[0]
            doc["elb.target_ip"] = doc["elb.target_ip"].split(':')[0]
            doc["elb.request_method"],doc["elb.request_url"],doc["elb.request_protocol"] = doc["elb.request"].split()
            
            actions.append(
                {"_index": INDEX_PREFIX,"_source": doc})

        try:
            helpers.bulk(es, actions)
            print("data were pushed successfully")
        except Exception as e:
            print("push data failed:",e)
        else:
            print("bulk elastic done")