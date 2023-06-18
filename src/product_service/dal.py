# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from pprint import pprint
import os
import boto3
from botocore.exceptions import ClientError
import uuid
import json
import logger
import random
import threading
from utils import get_tenant_id

from product_service.models import Product
from types import SimpleNamespace
from boto3.dynamodb.conditions import Key


is_pooled_deploy = os.environ['IS_POOLED_DEPLOY']
table_name = os.environ['TABLE_PRODUCTTABLE']
products_table = boto3.resource('dynamodb').Table(table_name)

suffix_start = 1 
suffix_end = 10

def get_product(event, productId):
    tenantId = get_tenant_id(event)
    try:
        logger.log_with_tenant_context(event, tenantId)
        logger.log_with_tenant_context(event, productId)
        response = products_table.get_item(Key= {
            'shardId': tenantId, 
            'productId': productId
        })
        item = response['Item']
        product = Product(item['shardId'], item['productId'], item['sku'], item['name'], item['price'], item['category'])
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error getting a product', e)
    else:
        logger.info("GetItem succeeded:"+ str(product))
        return product

def delete_product(event, productId):
    tenantId = get_tenant_id(event)

    try:
        response = products_table.delete_item(Key= {
            'shardId':tenantId, 
            'productId': productId
            })
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error deleting a product', e)
    else:
        logger.info("DeleteItem succeeded:")
        return response


def create_product(event, payload):
    tenantId = get_tenant_id(event)
    
    product = Product(tenantId, str(uuid.uuid4()), payload.sku,payload.name, payload.price, payload.category)
    
    try:
        response = products_table.put_item(
            Item=
                {
                    'shardId': tenantId,  
                    'productId': product.productId,
                    'sku': product.sku,
                    'name': product.name,
                    'price': product.price,
                    'category': product.category
                }
        )
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error adding a product', e)
    else:
        logger.info("PutItem succeeded:")
        return product

def update_product(event, payload, productId):
    try:
        tenantId = get_tenant_id(event)
        logger.log_with_tenant_context(event, tenantId)
        logger.log_with_tenant_context(event, productId)

        product = Product(tenantId,productId,payload.sku, payload.name, payload.price, payload.category)

        response = products_table.update_item(Key= {
            'shardId':product.shardId, 
            'productId': product.productId
        },
        UpdateExpression="set sku=:sku, #n=:productName, price=:price, category=:category",
        ExpressionAttributeNames= {'#n':'name'},
        ExpressionAttributeValues={
            ':sku': product.sku,
            ':productName': product.name,
            ':price': product.price,
            ':category': product.category
        },
        ReturnValues="UPDATED_NEW")
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error updating a product', e)
    else:
        logger.info("UpdateItem succeeded:")
        return product        

def get_products(event):
    tenantId = get_tenant_id(event) 
    get_all_products_response =[]
    try:
        __get_tenant_data(tenantId, get_all_products_response, products_table)
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error getting all products', e)
    else:
        logger.info("Get products succeeded")
        return get_all_products_response

def __get_tenant_data(partition_id, get_all_products_response, table):    
    logger.info(partition_id)
    response = table.query(KeyConditionExpression=Key('shardId').eq(partition_id))    
    if (len(response['Items']) > 0):
        for item in response['Items']:
            product = Product(item['shardId'], item['productId'], item['sku'], item['name'], item['price'], item['category'])
            get_all_products_response.append(product)
