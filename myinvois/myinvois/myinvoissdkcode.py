import frappe
import os
# frappe.init(site="prod.erpgulf.com")
# frappe.connect()
from myinvois.myinvois.createxml_sdk import xml_tags,salesinvoice_data,set_total_amounts,set_tax_type_main_form,invoice_Typecode_Simplified,invoice_Typecode_Standard,doc_Reference,additional_Reference ,company_Data,customer_Data,delivery_And_PaymentMeans,tax_Data,item_data,xml_structuring,invoice_Typecode_Compliance,delivery_And_PaymentMeans_for_Compliance,doc_Reference_compliance,get_tax_total_from_items
# from myinvois.myinvois.compliance import get_pwd,set_cert_path,create_compliance_x509,check_compliance
import xml.etree.ElementTree as ET
import base64
from frappe.utils import now
import re
from lxml import etree
import xml.dom.minidom as minidom
from datetime import datetime
import xml.etree.ElementTree as ET
import json
import xml.etree.ElementTree as ElementTree
from frappe.utils import execute_in_shell
import sys
import frappe 
import requests
from frappe.utils.data import  get_time
import base64
import pyqrcode


@frappe.whitelist(allow_guest=True)          
def myinvois_Background_on_submit(doc, method=None):              
# def zatca_Background(invoice_number):
                    
                    try:
                        sales_invoice_doc = doc
                        invoice_number = sales_invoice_doc.name
                        settings = frappe.get_doc('Zatca setting')
                        tax_rate = float(sales_invoice_doc.taxes[0].rate)

                        # if f"{tax_rate:.2f}" not in ['5.00', '15.00']:
                        #     if sales_invoice_doc.custom_zatca_tax_category not in ["Zero Rated", "Exempted","Services outside scope of tax / Not subject to VAT"]:
                        #         frappe.throw("Zatca tax category should be 'zero rated' or 'Exempted'or 'Services outside scope of tax / Not subject to VAT'.")

                        # if f"{tax_rate:.2f}" == '15.00':
                        #     if sales_invoice_doc.custom_zatca_tax_category != "Standard":
                        #         frappe.throw("Check the Zatca category code and enable it as standard.")

                        # if settings.zatca_invoice_enabled != 1:
                        #     frappe.throw("Zatca Invoice is not enabled in Zatca Settings, Please contact your system administrator")
                        
                        # if not frappe.db.exists("Sales Invoice", invoice_number):
                        #         frappe.throw("Please save and submit the invoice before sending to Zatca:  " + str(invoice_number))
                                
                        # sales_invoice_doc= frappe.get_doc("Sales Invoice",invoice_number )
            
                        # if sales_invoice_doc.docstatus in [0,2]:
                        #     frappe.throw("Please submit the invoice before sending to Zatca:  " + str(invoice_number))
                            
                        # if sales_invoice_doc.custom_zatca_status == "REPORTED" or sales_invoice_doc.custom_zatca_status == "CLEARED":
                        #     frappe.throw("Already submitted to Zakat and Tax Authority")
                        
                        myinvois_Call(invoice_number,0)
                        
                    except Exception as e:
                        frappe.throw("Error in background call:  " + str(e) )


# working on b2b
#compliance_type is invoice_type
 
@frappe.whitelist(allow_guest=True)
def myinvois_Call(invoice_number, compliance_type):
    try:
        print("enter in myinvoice call method")

        if not frappe.db.exists("Sales Invoice", invoice_number):
            frappe.throw("Invoice Number is NOT Valid: " + str(invoice_number))

        
        # Initialize the XML document
        # invoice = ET.Element("Invoice")
        invoice= xml_tags()
        
        # Fetch Sales Invoice data
        invoice, sales_invoice_doc = salesinvoice_data(invoice, invoice_number)
        print("INVOICE")
        print(ET.tostring(invoice, encoding='unicode'))
        print("sales invoice")
        print(sales_invoice_doc)

        # Fetch Customer data
        customer_doc = frappe.get_doc("Customer", sales_invoice_doc.customer)
        print("customer", customer_doc)

        # Set invoice type code based on compliance type and customer type
        if compliance_type == "0":
            print("enter in if")
            if customer_doc.custom_b2c == 1:
                invoice = invoice_Typecode_Simplified(invoice, sales_invoice_doc)
            else:
                invoice = invoice_Typecode_Standard(invoice, sales_invoice_doc)
        else:  # if it is a compliance test
            invoice = invoice_Typecode_Compliance(invoice, compliance_type)
            # print("enter in else", ET.tostring(invoice, encoding='unicode'))

        # Populate the XML with other required data
        invoice = company_Data(invoice, sales_invoice_doc)   # supplier data
        # print("Company Data",ET.tostring(invoice, encoding='unicode'))
        invoice = customer_Data(invoice, sales_invoice_doc)   # customer data
        # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))

        invoice = item_data(invoice, sales_invoice_doc)      # item data
        # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        invoice = doc_Reference(invoice, sales_invoice_doc, invoice_number)   # invoice currency code
        
        invoice = set_total_amounts(invoice, sales_invoice_doc)   # total amount incl & excl
        
        invoice = set_tax_type_main_form(invoice, sales_invoice_doc)  # tax type for main form

        # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        #Convert XML to pretty string
        pretty_xml_string = xml_structuring(invoice, sales_invoice_doc)
        print(pretty_xml_string)

        # You might want to return or save the pretty_xml_string as needed
        # return pretty_xml_string

    except Exception as e:
        print("ERROR: " + str(e))
        frappe.log_error(title='LHDN invoice call failed', message=get_traceback())

