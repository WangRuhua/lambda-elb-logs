rm -rf elb*.zip
zip -ru elblog2es.zip *
aws lambda update-function-code \
    --function-name  ${function_name}\
    --zip-file fileb://elblog2es.zip --region us-east-1