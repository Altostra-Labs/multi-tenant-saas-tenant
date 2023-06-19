# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import utils
import logger
import metrics_manager
import order_service.dal as order_service_dal
from aws_lambda_powertools import Tracer
tracer = Tracer()

@tracer.capture_lambda_handler
def get_order(event, context):
    tenantId = utils.get_tenant_id(event)
    tracer.put_annotation(key="TenantId", value=tenantId)

    logger.log_with_tenant_context(event, "Request received to get a order")
    params = event['pathParameters']
    id = params['id']
    logger.log_with_tenant_context(event, params)
    order = order_service_dal.get_order(event, id)

    logger.log_with_tenant_context(event, "Request completed to get a order")
    metrics_manager.record_metric(event, "SingleOrderRequested", "Count", 1)
    return utils.generate_response(order)
    
@tracer.capture_lambda_handler
def create_order(event, context):  
    tenantId = utils.get_tenant_id(event)
    tracer.put_annotation(key="TenantId", value=tenantId)

    logger.log_with_tenant_context(event, "Request received to create a order")
    payload = utils.load_body_json(event['body'])
    order = order_service_dal.create_order(event, payload)
    logger.log_with_tenant_context(event, "Request completed to create a order")
    metrics_manager.record_metric(event, "OrderCreated", "Count", 1)
    return utils.generate_response(order)
    
@tracer.capture_lambda_handler
def update_order(event, context):
    tenantId = utils.get_tenant_id(event)
    tracer.put_annotation(key="TenantId", value=tenantId)
    
    logger.log_with_tenant_context(event, "Request received to update a order")
    payload = utils.load_body_json(event['body'])
    params = event['pathParameters']
    id = params['id']
    order = order_service_dal.update_order(event, payload, id)
    logger.log_with_tenant_context(event, "Request completed to update a order") 
    metrics_manager.record_metric(event, "OrderUpdated", "Count", 1)   
    return utils.generate_response(order)

@tracer.capture_lambda_handler
def delete_order(event, context):
    tenantId = utils.get_tenant_id(event)

    tracer.put_annotation(key="TenantId", value=tenantId)

    logger.log_with_tenant_context(event, "Request received to delete a order")
    params = event['pathParameters']
    id = params['id']
    response = order_service_dal.delete_order(event, id)
    logger.log_with_tenant_context(event, "Request completed to delete a order")
    metrics_manager.record_metric(event, "OrderDeleted", "Count", 1)
    return utils.create_success_response("Successfully deleted the order")

@tracer.capture_lambda_handler
def get_orders(event, context):
    logger.log_with_tenant_context(event, "Request received to get all orders")
    response = order_service_dal.get_orders(event)
    metrics_manager.record_metric(event, "OrdersRetrieved", "Count", len(response))
    logger.log_with_tenant_context(event, "Request completed to get all orders")
    return utils.generate_response(response)

  