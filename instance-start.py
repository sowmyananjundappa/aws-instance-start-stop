#coding=utf-8
import boto3
import json
import smtplib
import time
from smtplib import SMTPException
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email.MIMEMultipart import MIMEMultipart
from email import encoders
from email.utils import COMMASPACE, formatdate
from slackclient import SlackClient
from botocore.exceptions import ClientError
SLACK_API_TOKEN = "*********************************"
sc = SlackClient(SLACK_API_TOKEN)
def mail(text):
    sender = 'mail id'
    receivers = ['mail id']
    msg = MIMEMultipart()
    msg['Subject'] = 'aws alert %s' %now
    msg['From'] = sender
    msg['To'] = ', '.join(receivers)
    msg.attach(MIMEText(text))
    try:
        smtpObj = smtplib.SMTP('mail relay name', 25)
        smtpObj.sendmail(sender, receivers, msg.as_string())
        print "Successfully sent email"
    except SMTPException:
        print "Error: unable to send email"
def slack_msg(message):
    sc.api_call("chat.postMessage", channel="#test", text=message)
def get_assume_arn_to_keys(Account_Number,Account_Name,ARN):
    sts_client = boto3.client('sts')
    response = sts_client.assume_role(
        DurationSeconds=3600,ExternalId=Account_Name,
        Policy='{"Version":"2012-10-17","Statement":[{"Sid":"Stmt1","Effect":"Allow","Action":"ec2:*","Resource":"*"}]}',
        RoleArn=ARN,RoleSessionName=Account_Name)
    aws_account_number = Account_Number
    aws_access_key = response['Credentials']['AccessKeyId']
    aws_secret_key = response['Credentials']['SecretAccessKey']
    aws_session_token = response['Credentials']['SessionToken']
    return (aws_account_number,aws_access_key,aws_secret_key,aws_session_token)
def ec2_instance():
    with open('/path/for/aws/role/details.json') as ec2_file:
        ec2_data = json.load(ec2_file)
        for index in range(len(ec2_data['Items'])):
            Account_Number = ec2_data['Items'][index]['Aws_Account_Number']
            Account_Name = ec2_data['Items'][index]['Acc_Name']
            ARN = ec2_data['Items'][index]['ARN']
            instance_id = ec2_data['Items'][index]['Instance_id']
            time = ec2_data['Items'][index]['Time']
            Name = ec2_data['Items'][index]['Server_Name']
            b = get_assume_arn_to_keys(Account_Number,Account_Name,ARN)
            client = boto3.client('ec2',aws_access_key_id=b[1],aws_secret_access_key=b[2],region_name='eu-west-1',aws_session_token=b[3])
            res = client.describe_instances(InstanceIds=[instance_id])
            state = res['Reservations'][0]['Instances'][0]['State']['Name']
            ip = res['Reservations'][0]['Instances'][0]['PrivateIpAddress']
            if state == 'stopped':
                try:
                    resp = client.start_instances(InstanceIds=[instance_id])
                    start = (resp['StartingInstances'][0]['CurrentState']['Name'])
                    print("Instance was in stopped stop, it's now started")
                    line = " Ec2 instance start is running"
                    slack_msg(line)
                    mail(line)
                    print(resp['StartingInstances'][0]['PreviousState']['Name'])
                except ClientError as e:
                    print(e)
            elif state == 'pending':
                print(ip," host is starting")
                msgs = Name + ip+" host is starting"
                slack_msg(msgs)
            else:
                print(ip," host is up and running no action required")
                msges = Name + ip+ " host is up and running no action required"
                linee = " Ec2 instance start is running"
                slack_msg(msges)
                mail(linee)
ec2_instance()
