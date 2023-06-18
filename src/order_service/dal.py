# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

from pprint import pprint
import os
import boto3
from botocore.exceptions import ClientError
import uuid
from order_service.models import Order
import json
import utils
from utils import get_tenant_id
from types import SimpleNamespace
import logger
import random
import threading
from boto3.dynamodb.conditions import Key

is_pooled_deploy = os.environ['IS_POOLED_DEPLOY']
table_name = os.environ['TABLE_ORDERTABLE']

dynamodb = boto3.resource('dynamodb')
orders_table = dynamodb.Table(table_name)

suffix_start = 1 
suffix_end = 10
 

def get_order(event, orderId):
    try:
        tenant_id = get_tenant_id(event)
        logger.log_with_tenant_context(event, tenant_id)
        logger.log_with_tenant_context(event, orderId)
        response = orders_table.get_item(Key= {
            'shardId': tenant_id, 
            'orderId': orderId,
        })

        item = response['Item']
        order = Order(item['shardId'], item['orderId'], item['orderName'], item['orderProducts'])

    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error getting a order', e)
    else:
        return order

def delete_order(event, orderId):
    table = __get_dynamodb_table(event, dynamodb)
    
    try:
        tenant_id = get_tenant_id(event)
        response = table.delete_item(Key= {
            'shardId':tenant_id, 
            'orderId': orderId,
        })

    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error deleting a order', e)
    else:
        logger.info("DeleteItem succeeded:")
        return response


def create_order(event, payload):
    tenantId = get_tenant_id(event)
    
    order = Order(tenantId, str(uuid.uuid4()), payload.orderName, payload.orderProducts)

    try:
        response = orders_table.put_item(Item= {
            'shardId':tenantId,
            'orderId': order.orderId, 
            'orderName': order.orderName,
            'orderProducts': get_order_products_dict(order.orderProducts)
        })

    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error adding a order', e)
    else:
        logger.info("PutItem succeeded:")
        return order

def update_order(event, payload, orderId):
    try:
        tenant_id = get_tenant_id(event)
        logger.log_with_tenant_context(event, tenant_id)
        logger.log_with_tenant_context(event, orderId)
        
        order = Order(tenant_id, orderId,payload.orderName, payload.orderProducts)
        response = orders_table.update_item(Key= {
            'shardId':order.shardId, 
            'orderId': order.orderId
        },
        UpdateExpression="set orderName=:orderName, "
        +"orderProducts=:orderProducts",
        ExpressionAttributeValues={
            ':orderName': order.orderName,
            ':orderProducts': get_order_products_dict(order.orderProducts)
        },
        ReturnValues="UPDATED_NEW")
    except ClientError as e:
        logger.error(e.response['Error']['Message'])
        raise Exception('Error updating a order', e)
    else:
        logger.info("UpdateItem succeeded:")
        return order

def get_orders(event):
    get_all_products_response = []
    tenantId = get_tenant_id(event)

    try:
        __get_tenant_data(tenantId, get_all_products_response, orders_table)
    except ClientError as e:
        logger.error()
        raise Exception('Error getting all orders', e) 
    else:
        logger.info("Get orders succeeded")
        return get_all_products_response
    
           
def __get_tenant_data(partition_id, get_all_products_response, table):    
    logger.info(partition_id)
    response = table.query(KeyConditionExpression=Key('shardId').eq(partition_id))    
    if (len(response['Items']) > 0):
        for item in response['Items']:
            order = Order(item['shardId'], item['orderId'], item['orderName'], item['orderProducts'])
            get_all_products_response.append(order)


def get_order_products_dict(orderProducts):
    orderProductList = []
    for i in range(len(orderProducts)):
        product = orderProducts[i]
        orderProductList.append(vars(product))
    return orderProductList    
