import boto3
from botocore.client import Config
import StringIO
import zipfile
import mimetypes



def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:568836648543:deployPortfolioTopic')
    
    # set default locations while creating the dictionary
    
    location = {
        "bucketName": 'porfoliobuild.miketest',
        "objectKey" : 'portfoliobuild.zip'
    }
    
    try:
        job = event.get("CodePipeline.job")
        
        if job:
            for artifact in job["data"]["inputArtifacts"]:
                if artifact["name"] == "MyAppBuild":
                    location = artifact["location"]["s3Location"]
         
        #Save in the logs where we built from, just in case         
        print "Building portfolio from " + str(location)  
        
        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))
    
        portfolio_bucket = s3.Bucket('portfolio.mikestest.online')
        build_bucket = s3.Bucket(location["bucketName"])
        
        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj(location["objectKey"], portfolio_zip)
        
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                  ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
        
        print "New Portfolio Deployed, sending SNS"
        topic.publish(Subject="New Portfolio Code Deployed", Message="New portfolio code was deployed to the production S3 bucket")
        if job:
            codepipeline = boto3.client("codepipeline")
            codepipeline.put_job_success_result(jobId=job["id"])
        
    except:
        topic.publish(Subject="portfolio deploy failed", Message="New portfolio code failed to deploy to the production S3 bucket")
        raise
        
    return 'Hello from Lambda'