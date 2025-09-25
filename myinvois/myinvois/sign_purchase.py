import frappe
import os
import hashlib
import base64
import lxml.etree as MyTree
import xml.etree.ElementTree as ET
import pyqrcode
import binascii
import json
import requests
# import asn1
import re
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ElementTree
import sys
import qrcode
import datetime


from datetime import datetime, timezone, timedelta
from lxml import etree

from myinvois.myinvois.purchasexml import xml_tags, purchase_invoice_data, doc_Reference, company_Data, customer_Data, xml_structuring
from myinvois.myinvois.createxml  import tax_Data, item_data, invoice_Typecode_Compliance, get_tax_total_from_items
from myinvois.myinvois.sign_invoice import gen_qrcode, get_invoice_version, get_API_url, get_access_token,make_qr_code_url, remove_api_from_url, removeTags, canonicalize_xml, getInvoiceHash, certificate_data, sign_data, ubl_extension_string, signed_properties_hash, xml_hash
from cryptography import x509
from cryptography.hazmat._oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.bindings._rust import ObjectIdentifier
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import utils
from frappe.utils import now
from frappe.utils import execute_in_shell
from frappe.utils.data import  get_time
from urllib.parse import urlparse, urlunparse
from io import BytesIO
from OpenSSL import crypto
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509 import load_pem_x509_certificate
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, BestAvailableEncryption, PrivateFormat




@frappe.whitelist()
def lhdn_Cancel_Background(uuid, invoice_number, reason="Document cancel"):
    try:
        purchase_doc = frappe.get_doc("Purchase Invoice", invoice_number)
        company_name = purchase_doc.company

        # Call method to get access token
        token = get_access_token(company_name)

        headers = {
            'accept': 'application/json',
            'Accept-Language': 'en',
            'X-Rate-Limit-Limit': '1000',
            'Authorization': f"Bearer {token}",
            'Content-Type': 'application/json'
        }

        # Get API version and form URL for cancellation
        invoice_version = get_invoice_version()
        cancel_api_url = get_API_url(base_url=f"/api/{invoice_version}/documents/state/{uuid}/state")

        # Prepare payload for cancel request
        payload = {
            "status": "cancelled",
            "reason": reason
        }

        # Send PUT request to cancel document with payload
        cancel_response = requests.put(cancel_api_url, headers=headers, json=payload)
        response_text = cancel_response.text

        # Check response status
        if cancel_response.status_code == 200:
            response_data = cancel_response.json()
            doc_status = response_data.get("status")
            purchase_doc.db_set("custom_lhdn_status", doc_status)
            frappe.msgprint(f"Document canceled successfully.<br>Status: {doc_status}<br>Response: {response_text}")
        else:
            frappe.msgprint(f"Failed to cancel document.<br>Status Code: {cancel_response.status_code}<br>Response: {response_text}")
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), ("Error in Cancel Document API"))
        frappe.throw(("An error occurred while canceling the document: ") + str(e))



@frappe.whitelist()     
def refresh_doc_status(uuid,invoice_number):
    try:
        print("enter in refersh")
        purchase_doc = frappe.get_doc("Purchase Invoice", invoice_number)
        company_name = purchase_doc.company
        long_id = purchase_doc.custom_long_id

        #calling token method
        token = get_access_token(company_name)

        headers = {
                    'accept': 'application/json',
                    'Accept-Language': 'en',
                    'X-Rate-Limit-Limit': '1000',
                    # 'Accept-Version': 'V2',
                    'Authorization': f"Bearer {token}",
                    'Content-Type': 'application/json'
                }
        invoice_version = get_invoice_version()
        #https://{{apiBaseUrl}}/api/v1.0/documents/51W5N1C6SCZ9AHBK39YQF03J10/details
        api_url = get_API_url(base_url=f"/api/{invoice_version}/documents/{uuid}/details")
        status_response = requests.get(api_url, headers=headers)
        response_text = status_response.text

      
        print("doc status",status_response)
        status_data = status_response.json()
        doc_status = status_data.get("status")
        long_id = status_data.get("longId")
        print("status code longid",status_data.get("longId"))

        purchase_doc.db_set("custom_lhdn_status", doc_status)

        if doc_status == "Valid":
            
            if uuid and long_id:
                qr_code_url = make_qr_code_url(uuid,long_id)
                #remove -api
                url = remove_api_from_url(qr_code_url)
                
                purchase_doc.db_set("custom_qr_code_link",url)
                # frappe.msgprint("Qr Code Updated")
                frappe.msgprint(f"Status: {doc_status}<br>Message : QR Code Url Updated<br>Response: {response_text}")

        else:
            frappe.msgprint(f"Status: {doc_status}<br>Message : QR Code Url Updated<br>Response: {response_text}")
  
            
    except Exception as e:
                    frappe.throw("ERROR in clearance invoice ,lhdn validation:  " + str(e) )



def compliance_api_call(invoice_number):
    try:
        print("enter in compliance call", invoice_number)
        sale_doc = frappe.get_doc("Purchase Invoice", invoice_number)
        company_name = sale_doc.company

        
        
        invoice_version = get_invoice_version()
        print("compliance method",invoice_version)
        
        #calling token method
        token = get_access_token(company_name)


        with open(frappe.local.site + "/private/files/output.xml", 'rb') as f:
            xml_data = f.read()

        sha256_hash = hashlib.sha256(xml_data).hexdigest()
        # print(sha256_hash)
        encoded_xml = base64.b64encode(xml_data).decode('utf-8')
        # print(encoded_xml)

        encoded_hash = sha256_hash
        signed_xmlfile_name = encoded_xml
        print("final hash",encoded_hash)
        print("final base64 xml",signed_xmlfile_name)


        if token:                 
            payload = {
                        "documents": [
                            {
                                "format": "XML",
                                "documentHash": encoded_hash,
                                "codeNumber": invoice_number,
                                "document": signed_xmlfile_name,  # Replace with actual Base64 encoded value
                            }
                        ]
                    }
            payload_json = json.dumps(payload)
            
            
            headers = {
                'accept': 'application/json',
                'Accept-Language': 'en',
                'X-Rate-Limit-Limit': '1000',
                # 'Accept-Version': 'V2',
                'Authorization': f"Bearer {token}",
                'Content-Type': 'application/json'
            }
        else:
            frappe.throw("Token for company {} not found".format(company_name))
        try:
            
            
            frappe.publish_progress(25, title='Progressing', description='wait sometime')

            ## First Api
            api_url = get_API_url(base_url=f"/api/{invoice_version}/documentsubmissions")
            response = requests.post(api_url, headers=headers, data=payload_json)

            response_text = response.text
            response_status_code= response.status_code

            print("checking reposnse",response_text)
            print("response.status_code",response.status_code)



            frappe.publish_progress(50, title='Progressing', description='wait sometime')

            #Handling Response
            if response_status_code == 202:
                frappe.publish_progress(100, title='Progressing', description='wait sometime')

                # Parse the JSON response
                response_data = json.loads(response_text)
                
                # Extract submissionUid and uuid
                submission_uid = response_data.get("submissionUid")
                accepted_documents = response_data.get("acceptedDocuments", [])
                rejected_documents = response_data.get("rejectedDocuments", [])
                                                
                
                
                #Document
                if accepted_documents:
                    print ("enter in accepted doc")
                    uuid = accepted_documents[0].get("uuid")
                    
                    # Update the Sales Invoice document with submissionUid and uuid
                    sale_doc.db_set("custom_submissionuid", submission_uid)  
                    sale_doc.db_set("custom_uuid", uuid) 

                    #Get Document Details Api call
                    api_url = get_API_url(base_url=f"/api/{invoice_version}/documents/{uuid}/details")
                    status_api_response = requests.get(api_url, headers=headers)                                
                    print("doc status",status_api_response)
                    status_data = status_api_response.json()

                    
                    doc_status = status_data.get("status")
                    long_id = status_data.get("longId")
                    sale_doc.db_set("custom_long_id", long_id)

                    #{envbaseurl}/uuid-of-document/share/longid
                    #https://preprod.myinvois.hasil.gov.my/GFSV5S3DR07TMXCS7033GA3J10/share/NZR8D94N3JW93KKX7033GA3J10hr8g6D1721560566"

                    if doc_status == 'Valid':

                        print("enter in valid")
                        if uuid and long_id:
                            qr_code_url = make_qr_code_url(uuid,long_id)
                            #remove -api
                            url = remove_api_from_url(qr_code_url)
                            
                            sale_doc.db_set("custom_lhdn_status", doc_status)
                            sale_doc.db_set("custom_qr_code_link",url)                        
                            frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Message : QR Code Url Updated<br>Response: {response_text}")

                    else:

                        print("enter in else validation")
                        doc_status = "InProgress"
                        sale_doc.db_set("custom_lhdn_status", doc_status)  

                        frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Response: <br>{response_text}")
                
                if rejected_documents:
                    frappe.publish_progress(100, title='Progressing', description='wait sometime')


                    print("enter in rejected doc")
                    doc_status = "Rejected"
                    sale_doc.db_set("custom_lhdn_status", doc_status)  

                    frappe.msgprint(f"Document Status: {doc_status}<br>Response: <br>{response_text}")


            else:
                frappe.throw("Error in complaince: " + str(response.text))    
        
        except Exception as e:
            frappe.msgprint(str(e))
            return "error in compliance", "NOT ACCEPTED"
    except Exception as e:
        frappe.throw("ERROR in clearance invoice ,lhdn validation:  " + str(e) )


@frappe.whitelist(allow_guest=True)
# def myinvois_Call(invoice_number, compliance_type):
def myinvois_Call(invoice_number):

    try:
        print("Purchase invoice myinvois call",invoice_number)

        # compliance_type = 1
        # any_item_has_tax_template = False

        if not frappe.db.exists("Purchase Invoice", invoice_number):
            frappe.throw("Invoice Number is NOT Valid: " + str(invoice_number))

        
        invoice= xml_tags()
        # print(ET.tostring(invoice, encoding='unicode'))
        
        # Fetch Sales Invoice data based on invoice type
        compliance_type,invoice,purchase_invoice_doc = purchase_invoice_data(invoice, invoice_number)
        # print(ET.tostring(invoice, encoding='unicode'))        

        # Fetch Customer data
        # customer_doc = frappe.get_doc("Customer", sales_invoice_doc.customer)

        
        if compliance_type :
            invoice = invoice_Typecode_Compliance(invoice, compliance_type)


        invoice = doc_Reference(invoice, purchase_invoice_doc, invoice_number)   # invoice currency code

        invoice = company_Data(invoice, purchase_invoice_doc)   # supplier data


        invoice = customer_Data(invoice, purchase_invoice_doc)   # customer data

        invoice = tax_Data(invoice, purchase_invoice_doc)   #invoicelevel   
        
        invoice= item_data(invoice, purchase_invoice_doc)  # invoiceline data
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))  
                
        # if not any_item_has_tax_template:
        #     invoice = tax_Data(invoice, sales_invoice_doc)
        # else:
        #     invoice = tax_Data_with_template(invoice, sales_invoice_doc)
       
        

        # else:
        #     item_data_with_template(invoice,sales_invoice_doc)



        # if not any_item_has_tax_template:
        #         print("enter in if")
        #         invoice = tax_Data(invoice, sales_invoice_doc)
        # invoice = item_data(invoice, sales_invoice_doc)      # item data
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))

       

                
        # invoice = set_total_amounts(invoice, sales_invoice_doc)   # total amount incl & excl
        
        # invoice = set_tax_type_main_form(invoice, sales_invoice_doc)  # tax type for main form

        # # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        # #Convert XML to pretty string
        pretty_xml_string = xml_structuring(invoice, purchase_invoice_doc)

        with open(frappe.local.site + "/private/files/create.xml", 'r') as file:
                                    file_content = file.read()

        # print("file content",file_content)
        # print("file_content",file_content)
        
        tag_removed_xml = removeTags(file_content)
        # print("tag_removed_xml",tag_removed_xml)    
        


        canonicalized_xml = canonicalize_xml(tag_removed_xml)

        hash1, encoded_hash = getInvoiceHash(canonicalized_xml)  #this method first convert canonical to hash hex then base64
        line_xml, doc_hash = xml_hash()
        print("line_xml",line_xml)
        print("doc_hash",doc_hash)
        certificate_base64, formatted_issuer_name, x509_serial_number, cert_digest, signing_time,strPassword = certificate_data(purchase_invoice_doc.company)
        
        signature = sign_data(line_xml,strPassword)
        prop_cert_base64 = signed_properties_hash(signing_time, cert_digest, formatted_issuer_name, x509_serial_number)
        
        ubl_extension_string(doc_hash, prop_cert_base64, signature, certificate_base64, signing_time, cert_digest, formatted_issuer_name, x509_serial_number, line_xml)

        compliance_api_call(invoice_number)  #digital signature



    except Exception as e:
        print("ERROR: " + str(e))
        frappe.log_error(title='LHDN invoice call failed', message=get_traceback())


@frappe.whitelist()          
def lhdn_Background(invoice_number):
    
    try:
        print("enter in backgorund method")
        # sales_invoice_doc = doc
        # invoice_number = sales_invoice_doc.name
        purchase_invoice_doc= frappe.get_doc("Purchase Invoice",invoice_number )

        settings = frappe.get_doc('Lhdn Settings')
        invoice_version = settings.invoice_version
        print("invoice versionnnnnnnn",invoice_version)
        tax_rate = float(purchase_invoice_doc.taxes[0].rate)

        # if f"{tax_rate:.2f}"  not in ['5.00', '15.00']:
        #     if sales_invoice_doc.custom_zatca_tax_category not in ["Zero Rated", "Exempted","Services outside scope of tax / Not subject to VAT"]:
        #         frappe.throw("Zatca tax category should be 'zero rated' or 'Exempted'or 'Services outside scope of tax / Not subject to VAT'.")

        # if f"{tax_rate:.2f}" == '15.00':
        #     if sales_invoice_doc.custom_zatca_tax_category != "Standard":
        #         frappe.throw("Check the Zatca category code and enable it as standard.")

        if settings.lhdn_invoice_enabled != 1:
            print("seeting enabled",settings.lhdn_invoice_enabled)
            frappe.throw("Lhdn Invoice is not enabled in Lhdn Settings, Please contact your system administrator")
        
        if not frappe.db.exists("Purchase Invoice", invoice_number):
                frappe.throw("Please save and submit the invoice before sending to Lhdn:  " + str(invoice_number))
                

        # if sales_invoice_doc.docstatus in [0,2]:
        #     frappe.throw("Please submit the invoice before sending to Zatca:  " + str(invoice_number))
            
        # if sales_invoice_doc.custom_zatca_status == "REPORTED" or sales_invoice_doc.custom_zatca_status == "CLEARED":
        #     frappe.throw("Already submitted to Zakat and Tax Authority")
        
        
        #commenting out for now
        # compliance_type = sales_invoice_doc.custom_einvoice_code
        myinvois_Call(invoice_number)
        # myinvois_Call(invoice_number,compliance_type)
        # myinvois_Call(invoice_number,1)
        
    except Exception as e:
        frappe.throw("Error in background call:  " + str(e) )


    


@frappe.whitelist()     
def refresh_doc_status(uuid,invoice_number):
    try:
        print("enter in refersh")
        sale_doc = frappe.get_doc("Purchase Invoice", invoice_number)
        company_name = sale_doc.company
        long_id = sale_doc.custom_long_id

        #calling token method
        token = get_access_token(company_name)

        headers = {
                    'accept': 'application/json',
                    'Accept-Language': 'en',
                    'X-Rate-Limit-Limit': '1000',
                    # 'Accept-Version': 'V2',
                    'Authorization': f"Bearer {token}",
                    'Content-Type': 'application/json'
                }
        invoice_version = get_invoice_version()
        #https://{{apiBaseUrl}}/api/v1.0/documents/51W5N1C6SCZ9AHBK39YQF03J10/details
        api_url = get_API_url(base_url=f"/api/{invoice_version}/documents/{uuid}/details")
        status_response = requests.get(api_url, headers=headers)
        response_text = status_response.text

      
        print("doc status",status_response)
        status_data = status_response.json()
        doc_status = status_data.get("status")
        long_id = status_data.get("longId")
        print("status code longid",status_data.get("longId"))

        sale_doc.db_set("custom_lhdn_status", doc_status)

        if doc_status == "Valid":
            
            if uuid and long_id:
                qr_code_url = make_qr_code_url(uuid,long_id)
                #remove -api
                url = remove_api_from_url(qr_code_url)
                
                sale_doc.db_set("custom_qr_code_link",url)
                # frappe.msgprint("Qr Code Updated")
                frappe.msgprint(f"Status: {doc_status}<br>Message : QR Code Url Updated<br>Response: {response_text}")

        else:
            frappe.msgprint(f"Status: {doc_status}<br>Message : QR Code Url Updated<br>Response: {response_text}")
  
            
    except Exception as e:
                    frappe.throw("ERROR in clearance invoice ,lhdn validation:  " + str(e) )
