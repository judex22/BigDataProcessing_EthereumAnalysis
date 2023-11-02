"""Question - 1 PARTA-2
"""
import sys, string
import os
import socket
import time
import operator
import boto3
import json
from pyspark.sql import SparkSession
from datetime import datetime
import pandas as pd
import json

if __name__ == "__main__":

    spark = SparkSession\
        .builder\
        .appName("Q1_P2")\
        .getOrCreate()

    def good_line(line):
        try:
            fields = line.split(',')
            if len(fields)!=15:
                return False
            int(fields[11])
            return True
        except:
            return False

    # shared read-only object bucket containing datasets
    s3_data_repository_bucket = os.environ['DATA_REPOSITORY_BUCKET']

    s3_endpoint_url = os.environ['S3_ENDPOINT_URL']+':'+os.environ['BUCKET_PORT']
    s3_access_key_id = os.environ['AWS_ACCESS_KEY_ID']
    s3_secret_access_key = os.environ['AWS_SECRET_ACCESS_KEY']
    s3_bucket = os.environ['BUCKET_NAME']

    hadoopConf = spark.sparkContext._jsc.hadoopConfiguration()
    hadoopConf.set("fs.s3a.endpoint", s3_endpoint_url)
    hadoopConf.set("fs.s3a.access.key", s3_access_key_id)
    hadoopConf.set("fs.s3a.secret.key", s3_secret_access_key)
    hadoopConf.set("fs.s3a.path.style.access", "true")
    hadoopConf.set("fs.s3a.connection.ssl.enabled", "false")

    lines = spark.sparkContext.textFile("s3a://" + s3_data_repository_bucket + "/ECS765/ethereum-parvulus/transactions.csv")
    
    #lines = spark.sparkContext.textFile("s3a://" + s3_data_repository_bucket + "/ECS765")
    clean_lines = lines.filter(good_line)
    #dates = clean_lines.map(lambda b:(int(b.split(',')[11]/1000).strftime("%d-%m-%Y"),1))
    
    
    val = clean_lines.map(lambda b:((datetime.fromtimestamp(int(b.split(',')[11])).strftime("%m-%Y")  ,  (int(b.split(',')[7]),    1))))
    red = val.reduceByKey(lambda x, y: (x[0]+y[0], x[1]+y[1]))                                                     # adds the two entries of same date
    avg_tr = red.map(lambda a: (a[0], str(a[1][0]/a[1][1])))                                                # summation of all values of same date with count
    avg_tr = avg_tr.map(lambda z: ','.join(str(t) for t in z))                                                     # mapping of average values 




    now = datetime.now() # current date and time
    date_time = now.strftime("%d-%m-%Y_%H:%M:%S")

    my_bucket_resource = boto3.resource('s3',
                endpoint_url='http://' + s3_endpoint_url,
                aws_access_key_id=s3_access_key_id,
                aws_secret_access_key=s3_secret_access_key)

    my_result_object = my_bucket_resource.Object(s3_bucket,'Q1_P2' + date_time + '/partA_P2.txt')
    my_result_object.put(Body=json.dumps(avg_tr.take(100)))


    spark.stop()