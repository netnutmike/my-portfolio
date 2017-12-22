import boto3
from botocore.client import Config
import StringIO
import zipfile
import mimetypes



def lambda_handler(event, context):
    sns = boto3.resource('sns')
    topic = sns.Topic('arn:aws:sns:us-east-1:568836648543:deployPortfolioTopic')
    
    try:
        s3 = boto3.resource('s3', config=Config(signature_version='s3v4'))
    
        portfolio_bucket = s3.Bucket('portfolio.mikestest.online')
        build_bucket = s3.Bucket('porfoliobuild.miketest')
        
        portfolio_zip = StringIO.StringIO()
        build_bucket.download_fileobj('portfoliobuild.zip', portfolio_zip)
        
        with zipfile.ZipFile(portfolio_zip) as myzip:
            for nm in myzip.namelist():
                obj = myzip.open(nm)
                portfolio_bucket.upload_fileobj(obj, nm,
                  ExtraArgs={'ContentType': mimetypes.guess_type(nm)[0]})
                portfolio_bucket.Object(nm).Acl().put(ACL='public-read')
        
        print "New Portfolio Deployed, sending SNS"
        topic.publish(Subject="New Portfolio Code Deployed", Message="New portfolio code was deployed to the production S3 bucket")
        
    except:
        topic.publish(Subject="portfolio deploy failed", Message="New portfolio code failed to deploy to the production S3 bucket")
        raise
        
    return 'Hello from Lambda'