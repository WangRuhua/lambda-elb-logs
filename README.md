# lambda-elb-logs
<p>Parser and send AWS elb logs to elasticsearch</p>
latest ELB log fields: https://docs.aws.amazon.com/elasticloadbalancing/latest/application/load-balancer-access-logs.html#access-log-entry-format

# install python3.8  dependency
pip3 install -r requirements.txt

# AWS SAM 
https://aws.amazon.com/serverless/sam/

Install AWS sam, you can test your lambda on local
and easy to build and deploy to AWS

SAM template for Lambda:

https://docs.aws.amazon.com/lambda/latest/dg/with-s3-example-use-app-spec.html

Build and local invoke with event

``
sam build && sam local invoke  -e  event.json
``
