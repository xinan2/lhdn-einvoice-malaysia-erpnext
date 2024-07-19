from lxml import etree
import hashlib
import base64
import lxml.etree as MyTree
from datetime import datetime
import xml.etree.ElementTree as ET
import frappe
import os

from myinvois.myinvois.createxml import xml_tags,salesinvoice_data,set_total_amounts,set_tax_type_main_form,invoice_Typecode_Simplified,invoice_Typecode_Standard,doc_Reference,additional_Reference ,company_Data,customer_Data,delivery_And_PaymentMeans,tax_Data,item_data,xml_structuring,invoice_Typecode_Compliance,delivery_And_PaymentMeans_for_Compliance,doc_Reference_compliance,get_tax_total_from_items
import pyqrcode
import binascii

from cryptography import x509
from cryptography.hazmat._oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.bindings._rust import ObjectIdentifier
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
import json
import requests
from cryptography.hazmat.primitives import serialization
# import asn1


# frappe.init(site="prod.erpgulf.com")
# frappe.connect()
# from myinvois.myinvois.compliance import get_pwd,set_cert_path,create_compliance_x509,check_compliance


from frappe.utils import now
import re
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET
import json
import xml.etree.ElementTree as ElementTree
from frappe.utils import execute_in_shell
import sys
import frappe 
import requests
from frappe.utils.data import  get_time
from datetime import datetime, timedelta






def removeTags(finalzatcaxml):
                try:
                    #Code corrected by Farook K - ERPGulf
                    xml_file = MyTree.fromstring(finalzatcaxml)
                    xsl_file = MyTree.fromstring('''<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform"
                                    xmlns:xs="http://www.w3.org/2001/XMLSchema"
                                    xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
                                    xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
                                    xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
                                    xmlns:ext="urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2"
                                    exclude-result-prefixes="xs"
                                    version="2.0">
                                    <xsl:output omit-xml-declaration="yes" encoding="utf-8" indent="no"/>
                                    <xsl:template match="node() | @*">
                                        <xsl:copy>
                                            <xsl:apply-templates select="node() | @*"/>
                                        </xsl:copy>
                                    </xsl:template>
                                    <xsl:template match="//*[local-name()='Invoice']//*[local-name()='UBLExtensions']"></xsl:template>
                                    <xsl:template match="//*[local-name()='AdditionalDocumentReference'][cbc:ID[normalize-space(text()) = 'QR']]"></xsl:template>
                                        <xsl:template match="//*[local-name()='Invoice']/*[local-name()='Signature']"></xsl:template>
                                    </xsl:stylesheet>''')
                    transform = MyTree.XSLT(xsl_file.getroottree())
                    transformed_xml = transform(xml_file.getroottree())
                    return transformed_xml
                except Exception as e:
                                frappe.throw(" error in remove tags: "+ str(e) )
                




def canonicalize_xml (tag_removed_xml):
                try:
                    #Code corrected by Farook K - ERPGulf
                    canonical_xml = etree.tostring(tag_removed_xml, method="c14n").decode()
                    return canonical_xml    
                except Exception as e:
                            frappe.throw(" error in canonicalise xml: "+ str(e) )    





def getDoceHash_base64(canonicalized_xml):
    try:
        print("Enter in hash method")
        print("Next XML", canonicalized_xml)

        # Calculate SHA-256 hash of the canonicalized XML
        hash_object = hashlib.sha256(canonicalized_xml.encode())
        print("hash_object", hash_object)
        hash_hex = hash_object.hexdigest()
        print("hash_hex", hash_hex)

        # Base64 encode the canonicalized XML
        base64_encoded_xml = base64.b64encode(canonicalized_xml.encode()).decode('utf-8')
        print("base64_encoded_xml", base64_encoded_xml)

        return hash_hex, base64_encoded_xml
    except Exception as e:
        frappe.throw("Error in Invoice hash of xml: " + str(e))



def getInvoiceHash(canonicalized_xml):
        try:
            print("enter in hash method")
            print("Nexxxxxxxxxxxxxxxxx xml",canonicalized_xml)
            #Code corrected by Farook K - ERPGulf
            hash_object = hashlib.sha256(canonicalized_xml.encode())
            print("hash_object",hash_object)
            hash_hex = hash_object.hexdigest()
            print("hash_hex",hash_hex)
            hash_base64 = base64.b64encode(bytes.fromhex(hash_hex)).decode('utf-8')

            print("hash_base64",hash_base64)
            # base64_encoded = base64.b64encode(hash_hex.encode()).decode()
            return hash_hex,hash_base64
        except Exception as e:
                    frappe.throw(" error in Invoice hash of xml: "+ str(e) )


def xml_base64_Decode(signed_xmlfile_name):
                    try:
                        with open(signed_xmlfile_name, "r") as file:
                                        xml = file.read().lstrip()
                                        base64_encoded = base64.b64encode(xml.encode("utf-8"))
                                        base64_decoded = base64_encoded.decode("utf-8")
                                        return base64_decoded
                    except Exception as e:
                        frappe.msgprint("Error in xml base64:  " + str(e) )


@frappe.whitelist()
def get_access_token(company_name):
    # Fetch the credentials from the custom doctype
    credentials = frappe.get_doc("Lhdn Authorizations", company_name)
    client_id = credentials.client_id
    client_secret = credentials.get_password(fieldname='client_secret_key', raise_exception=False)   

    # # Check if token is already available and not expired
    if credentials.access_token and credentials.token_expiry:
        print("checking enter in first if")
        token_expiry = datetime.strptime(str(credentials.token_expiry), "%Y-%m-%d %H:%M:%S")
        print("token_expiry",token_expiry)
        if datetime.now() < token_expiry:
            print("second if")
            return credentials.access_token

    # # If token is expired or not available, request a new one
    # make url dynamic
    # get_API_url(base_url="/connect/token")
    response = requests.request("POST", url= get_API_url(base_url="/connect/token"), data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "InvoicingAPI"
    })

    # response = requests.post("https://{base_url}/connect/token", data={
    #     "client_id": client_id,
    #     "client_secret": client_secret,
    #     "grant_type": "client_credentials",
    #     "scope": "InvoicingAPI"
    # })
    print("response",response)

    if response.status_code == 200:
        data = response.json()
        access_token = data["access_token"]
        expires_in = data["expires_in"]
        token_expiry = datetime.now() + timedelta(seconds=expires_in)

        # Store the new token and expiry in the custom doctype
        credentials.access_token = access_token
        credentials.token_expiry = token_expiry.strftime("%Y-%m-%d %H:%M:%S")
        credentials.save()

        return access_token
    else:
        frappe.throw("Failed to fetch access token")


def compliance_api_call(encoded_hash,signed_xmlfile_name,invoice_number,invoice_version):
                try:

                    print("compliance method",invoice_version)

                    sale_doc = frappe.get_doc("Sales Invoice", invoice_number)
                   
                    #calling token method
                    token = get_access_token(sale_doc.company)
                   
                    print("hash",encoded_hash)
                    print("xml",signed_xmlfile_name)                   
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
                    
                    # company = settings.company
                    # company_name = frappe.db.get_value("Company", company, "abbr")
                    # basic_auth = settings.get("basic_auth", "{}")
                    # frappe.msgprint(basic_auth)
                    # basic_auth_data = json.loads(basic_auth)
                    # csid = get_csid_for_company(basic_auth_data, company_name)
                    # frappe.msgprint(csid)
                    # if csid:
                    # token = "eyJhbGciOiJSUzI1NiIsImtpZCI6Ijk2RjNBNjU2OEFEQzY0MzZDNjVBNDg1MUQ5REM0NTlFQTlCM0I1NTRSUzI1NiIsIng1dCI6Imx2T21Wb3JjWkRiR1draFIyZHhGbnFtenRWUSIsInR5cCI6ImF0K2p3dCJ9.eyJpc3MiOiJodHRwczovL3ByZXByb2QtaWRlbnRpdHkubXlpbnZvaXMuaGFzaWwuZ292Lm15IiwibmJmIjoxNzIxMTI2MDI2LCJpYXQiOjE3MjExMjYwMjYsImV4cCI6MTcyMTEyOTYyNiwiYXVkIjpbIkludm9pY2luZ0FQSSIsImh0dHBzOi8vcHJlcHJvZC1pZGVudGl0eS5teWludm9pcy5oYXNpbC5nb3YubXkvcmVzb3VyY2VzIl0sInNjb3BlIjpbIkludm9pY2luZ0FQSSJdLCJjbGllbnRfaWQiOiI0YzM3NjZkYy1iMDZjLTQ2MjItODUzOC01NmUyMTdlZTcyNjciLCJJc1RheFJlcHJlcyI6IjEiLCJJc0ludGVybWVkaWFyeSI6IjAiLCJJbnRlcm1lZElkIjoiMCIsIkludGVybWVkVElOIjoiIiwiSW50ZXJtZWRFbmZvcmNlZCI6IjIiLCJuYW1lIjoiQzEwODA2NTIxMDkwOjRjMzc2NmRjLWIwNmMtNDYyMi04NTM4LTU2ZTIxN2VlNzI2NyIsIlNTSWQiOiI1YmRiYjQ1Yy02Mjk5LTFiN2ItZTRhYS1mYmQwYThhZGQ1NTEiLCJwcmVmZXJyZWRfdXNlcm5hbWUiOiJFUlBOZXh0IiwiVGF4SWQiOiI4NjYiLCJUYXhUaW4iOiJDMTA4MDY1MjEwOTAiLCJQcm9mSWQiOiIyMDY4IiwiSXNUYXhBZG1pbiI6IjAiLCJJc1N5c3RlbSI6IjEiLCJOYXRJZCI6IiJ9.Q2A_WSJ_HiwJ5HGusTZ-mw3zGPgOOS7_e0IJr2-9IzD6XTfUKw7p9TvgIbkg2meF3V4lBngmTvTwVQuxQBt4ZBG4A07sOfsRaEAjqxfZRs16KOx3OtYrUnOLwj5fr0mLa4HMWnZJRam0KmpMjcaONC6p3CPoKtwBh-ofkHVUgcQIE3SmKnPs0t1zFhpfHt9hTd8U1qxWTnG1jmRDTcMFdCNq_fvO8g2YNcOt_1ddLqHqmsEDxzMfQPdJ8GLH-e_84Pr1GSWb3oRsrZqqG4z8t-9g9wbqgYydpfaeVzHppmvqEHYYhjPx8HTOvDIrsrOGmF0msiv6pDzdFv1-9TFStQ"
                    headers = {
                        'accept': 'application/json',
                        'Accept-Language': 'en',
                        'X-Rate-Limit-Limit': '1000',
                        # 'Accept-Version': 'V2',
                        'Authorization': f"Bearer {token}",
                        'Content-Type': 'application/json'
                    }
                    # else:
                    #     frappe.throw("CSID for company {} not found".format(company_name))
                    try:
                        # frappe.throw("inside compliance api call2")
                        # response = requests.request("POST", url=get_API_url(base_url="compliance/invoices"), headers=headers, data=payload)
                        api_url = get_API_url(base_url=f"/api/{invoice_version}/documentsubmissions")
                        response = requests.post(api_url, headers=headers, data=payload_json)

                        response_text = response.text
                        response_status = response.status_code

                        # frappe.msgprint(f"API Status: {response_status}\nResponse: {response_text}")
                        # frappe.msgprint(f"API Status: {response_status}\nResponse:\n{response_text}")

                        
                        if response_status == 202:
                            # Parse the JSON response
                            response_data = json.loads(response_text)
                            
                            # Extract submissionUid and uuid
                            submission_uid = response_data.get("submissionUid")
                            accepted_documents = response_data.get("acceptedDocuments", [])
                            
                            if accepted_documents:
                                uuid = accepted_documents[0].get("uuid")
                                
                                # Update the Sales Invoice document with submissionUid and uuid
                                sale_doc.db_set("custom_submissionuid", submission_uid)  
                                sale_doc.db_set("custom_uuid", uuid)        
                        
                            frappe.msgprint(f"API Status: {response_status}<br>Response: {response_text}")
                            # # Create a custom dialog
                            # dialog = frappe.ui.Dialog({
                            #     'title': 'API Response',
                            #     'fields': [
                            #         {'fieldname': 'message', 'fieldtype': 'HTML', 'options': f"<p>API Status: {response_status}<br>Response: {response_text}</p>"}
                            #     ],
                            #     'primary_action': lambda: fetch_document_status(sale_doc),
                            #     'primary_action_label': 'OK'
                            # })
                            # dialog.show()

                        else:
                            frappe.throw("Error in complaince: " + str(response.text))    
                    
                    except Exception as e:
                        frappe.msgprint(str(e))
                        return "error in compliance", "NOT ACCEPTED"
                except Exception as e:
                    frappe.throw("ERROR in clearance invoice ,lhdn validation:  " + str(e) )




def fetch_document_status(sale_doc):
    # Your API call to fetch the document status and update the Sales Invoice
    try:
        frappe.msgprint("fgfgfgf")
        # Replace with the actual API call to fetch the status
        # status_api_url = get_status_api_url(sale_doc.custom_submissionuid)
        # response = requests.get(status_api_url)

        # response_text = response.text
        # response_status = response.status_code

        # if response_status == 200:
        #     # Parse the response and update the Sales Invoice
        #     response_data = json.loads(response_text)
        #     document_status = response_data.get("status")
        #     sale_doc.db_set("document_status", document_status)

        #     frappe.msgprint(f"Document status updated: {document_status}")

        # else:
        #     frappe.throw("Error fetching document status: " + str(response.text))

    except Exception as e:
        frappe.msgprint(str(e))


def get_API_url(base_url):
                try:
                    settings =  frappe.get_doc('Lhdn Settings')
                    if settings.select == "Sandbox":
                        url = settings.sandbox_url + base_url
                    else:
                        url = settings.production_url + base_url
                    return url 
                except Exception as e:
                    frappe.throw(" getting url failed"+ str(e) ) 




@frappe.whitelist(allow_guest=True)          
# def myinvois_Background_on_submit(doc, method=None):              
def lhdn_Background(invoice_number):
                    
                    try:
                        print("enter in backgorund method")
                        # sales_invoice_doc = doc
                        # invoice_number = sales_invoice_doc.name
                        sales_invoice_doc= frappe.get_doc("Sales Invoice",invoice_number )

                        settings = frappe.get_doc('Lhdn Settings')
                        invoice_version = settings.invoice_version
                        print("invoice versionnnnnnnn",invoice_version)
                        tax_rate = float(sales_invoice_doc.taxes[0].rate)

                        # if f"{tax_rate:.2f}" not in ['5.00', '15.00']:
                        #     if sales_invoice_doc.custom_zatca_tax_category not in ["Zero Rated", "Exempted","Services outside scope of tax / Not subject to VAT"]:
                        #         frappe.throw("Zatca tax category should be 'zero rated' or 'Exempted'or 'Services outside scope of tax / Not subject to VAT'.")

                        # if f"{tax_rate:.2f}" == '15.00':
                        #     if sales_invoice_doc.custom_zatca_tax_category != "Standard":
                        #         frappe.throw("Check the Zatca category code and enable it as standard.")

                        if settings.lhdn_invoice_enabled != 1:
                            print("seeting enabled",settings.lhdn_invoice_enabled)
                            frappe.throw("Lhdn Invoice is not enabled in Lhdn Settings, Please contact your system administrator")
                        
                        if not frappe.db.exists("Sales Invoice", invoice_number):
                                frappe.throw("Please save and submit the invoice before sending to Lhdn:  " + str(invoice_number))
                                
            
                        # if sales_invoice_doc.docstatus in [0,2]:
                        #     frappe.throw("Please submit the invoice before sending to Zatca:  " + str(invoice_number))
                            
                        # if sales_invoice_doc.custom_zatca_status == "REPORTED" or sales_invoice_doc.custom_zatca_status == "CLEARED":
                        #     frappe.throw("Already submitted to Zakat and Tax Authority")
                        
                        myinvois_Call(invoice_number,invoice_version,1)
                        
                    except Exception as e:
                        frappe.throw("Error in background call:  " + str(e) )


# working on b2b
#compliance_type is invoice_type
 
@frappe.whitelist(allow_guest=True)
def myinvois_Call(invoice_number,invoice_version, compliance_type):
    try:
        print("enter in myinvoice call method")
        print("myinovi",invoice_version)

        compliance_type = 1
        # any_item_has_tax_template = False

        if not frappe.db.exists("Sales Invoice", invoice_number):
            frappe.throw("Invoice Number is NOT Valid: " + str(invoice_number))

        
        # Initialize the XML document
        # invoice = ET.Element("Invoice")
        invoice= xml_tags()
        # print(ET.tostring(invoice, encoding='unicode'))
        
        # Fetch Sales Invoice data
        invoice, sales_invoice_doc = salesinvoice_data(invoice, invoice_number)
        # print("INVOICE")
        # print(ET.tostring(invoice, encoding='unicode'))        

        # Fetch Customer data
        customer_doc = frappe.get_doc("Customer", sales_invoice_doc.customer)
        print("customer", customer_doc)

        # Set invoice type code based on compliance type and customer type
        # compliance type = B2B / B2C / B2G
        if compliance_type == "0":
            # print("enter in if")
            if customer_doc.custom_b2c == 1:
                invoice = invoice_Typecode_Simplified(invoice, sales_invoice_doc)
            else:
                invoice = invoice_Typecode_Standard(invoice, sales_invoice_doc)
        else:  # if it is a compliance test
            # print ("compiance type check")
            compliance_type = "1"
            invoice = invoice_Typecode_Compliance(invoice, compliance_type)
            # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        invoice = doc_Reference(invoice, sales_invoice_doc, invoice_number)   # invoice currency code
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))

        invoice = company_Data(invoice, sales_invoice_doc)   # supplier data
        # print("Company Data",ET.tostring(invoice, encoding='unicode'))


        invoice = customer_Data(invoice, sales_invoice_doc)   # customer data
        # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        invoice = tax_Data(invoice, sales_invoice_doc)   #invoicelevel   
        
        invoice=item_data(invoice,sales_invoice_doc)  # invoiceline data
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


        # # Populate the XML with other required data
        # invoice = company_Data(invoice, sales_invoice_doc)   # supplier data
        # # print("Company Data",ET.tostring(invoice, encoding='unicode'))
        # invoice = customer_Data(invoice, sales_invoice_doc)   # customer data
        # # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # # print("enter in else", ET.tostring(invoice, encoding='unicode'))

        

                
        # invoice = set_total_amounts(invoice, sales_invoice_doc)   # total amount incl & excl
        
        # invoice = set_tax_type_main_form(invoice, sales_invoice_doc)  # tax type for main form

        # # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        #Convert XML to pretty string
        pretty_xml_string = xml_structuring(invoice, sales_invoice_doc)
        #print(pretty_xml_string)

        # ###########################
        # #Starting code with new git
        # ##########################
        with open(frappe.local.site + "/private/files/finalzatcaxml.xml", 'r') as file:
                                    file_content = file.read()
        
        #print("file_content",file_content)
        tag_removed_xml = removeTags(file_content)
        #print("tag_removed_xml",tag_removed_xml)
        canonicalized_xml = canonicalize_xml(tag_removed_xml)
        #print("canonicalized_xml",canonicalized_xml)

        # hash1, encoded_hash = getInvoiceHash(canonicalized_xml)
        hash_hex, base64_encoded_xml = getDoceHash_base64(canonicalized_xml)
        # print("hash1",hash_hex)
        # compliance_api_call(encoded_hash, signed_xmlfile_name)
        
        compliance_api_call(hash_hex, base64_encoded_xml,invoice_number,invoice_version)



        # # You might want to return or save the pretty_xml_string as needed
        # # return pretty_xml_string

    except Exception as e:
        print("ERROR: " + str(e))
        frappe.log_error(title='LHDN invoice call failed', message=get_traceback())

























