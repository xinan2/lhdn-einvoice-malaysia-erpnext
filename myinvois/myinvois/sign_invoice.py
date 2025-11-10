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
from myinvois.myinvois.createxml import xml_tags,salesinvoice_data,doc_Reference,company_Data,customer_Data,tax_Data,item_data,xml_structuring,invoice_Typecode_Compliance,get_tax_total_from_items
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
def gen_qrcode(text):
    data = pyqrcode.create(text)

    return f'data:image/png;base64,{data.png_as_base64_str(scale=2)}'


@frappe.whitelist()
def lhdn_Cancel_Background(uuid, invoice_number, reason="Document cancel"):
    try:
        sale_doc = frappe.get_doc("Sales Invoice", invoice_number)
        company_name = sale_doc.company

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
            sale_doc.db_set("custom_lhdn_status", doc_status)
            frappe.msgprint(f"Document canceled successfully.<br>Status: {doc_status}<br>Response: {response_text}")
        else:
            frappe.msgprint(f"Failed to cancel document.<br>Status Code: {cancel_response.status_code}<br>Response: {response_text}")
    
    except Exception as e:
        frappe.log_error(frappe.get_traceback(), ("Error in Cancel Document API"))
        frappe.throw(("An error occurred while canceling the document: ") + str(e))

@frappe.whitelist()
def get_access_token(company_name):
    # Fetch the credentials from the custom doctype
    credentials = frappe.get_doc("Lhdn Authorizations", company_name)
    client_id = credentials.client_id
    client_secret = credentials.get_password(fieldname='client_secret_key', raise_exception=False)

    # Check if token is already available and not expired
    if credentials.access_token and credentials.token_expiry:
        token_expiry = datetime.strptime(str(credentials.token_expiry), "%Y-%m-%d %H:%M:%S")
        if datetime.now() < token_expiry:
            return credentials.access_token

    url = get_API_url(base_url="/connect/token")
    print("Request URL:", url)

    if credentials.custom_intermediary == 1:
        # For intermediary, add the onbehalfof header
        headers = {
            "onbehalfof": credentials.custom_tin_no
        }
        response = requests.request(
            "POST",
            url=url,
            headers=headers,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "InvoicingAPI"
            }
        )
    else:
        # Request without onbehalfof header
        response = requests.request(
            "POST",
            url=url,
            data={
                "client_id": client_id,
                "client_secret": client_secret,
                "grant_type": "client_credentials",
                "scope": "InvoicingAPI"
            }
        )

    print("Response Status Code:", response.status_code)
    print("Response Text:", response.text)
    print("Response Headers:", response.headers)

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
        frappe.throw(f"Failed to fetch access token. Error: {response.text}")

@frappe.whitelist()     
def refresh_doc_status(uuid,invoice_number):
    try:
        print("enter in refersh")
        sale_doc = frappe.get_doc("Sales Invoice", invoice_number)
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
        if long_id:
            sale_doc.db_set("custom_long_id", long_id)


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


@frappe.whitelist(allow_guest=True)          
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

        # if f"{tax_rate:.2f}"  not in ['5.00', '15.00']:
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
                        
        
        #commenting out for now
        # compliance_type = sales_invoice_doc.custom_einvoice_code
        myinvois_Call(invoice_number)
        # myinvois_Call(invoice_number,compliance_type)
        # myinvois_Call(invoice_number,1)
        
    except Exception as e:
        frappe.throw("Error in background call:  " + str(e) )


@frappe.whitelist(allow_guest=True)
# def myinvois_Call(invoice_number, compliance_type):
def myinvois_Call(invoice_number):

    try:
        print("enter in myinvoice call method")

        # compliance_type = 1
        # any_item_has_tax_template = False

        if not frappe.db.exists("Sales Invoice", invoice_number):
            frappe.throw("Invoice Number is NOT Valid: " + str(invoice_number))

        
        invoice= xml_tags()
        # print(ET.tostring(invoice, encoding='unicode'))
        
        # Fetch Sales Invoice data based on invoice type
        compliance_type,invoice,sales_invoice_doc = salesinvoice_data(invoice, invoice_number)
        # print(ET.tostring(invoice, encoding='unicode'))        

        # Fetch Customer data
        # customer_doc = frappe.get_doc("Customer", sales_invoice_doc.customer)

        
        if compliance_type :
            invoice = invoice_Typecode_Compliance(invoice, compliance_type)


        invoice = doc_Reference(invoice, sales_invoice_doc, invoice_number)   # invoice currency code

        invoice = company_Data(invoice, sales_invoice_doc)   # supplier data


        invoice = customer_Data(invoice, sales_invoice_doc)   # customer data

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

       

                
        # invoice = set_total_amounts(invoice, sales_invoice_doc)   # total amount incl & excl
        
        # invoice = set_tax_type_main_form(invoice, sales_invoice_doc)  # tax type for main form

        # # print("hhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhhh")
        # # print("enter in else", ET.tostring(invoice, encoding='unicode'))


        # #Convert XML to pretty string
        pretty_xml_string = xml_structuring(invoice, sales_invoice_doc)

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
        certificate_base64, formatted_issuer_name, x509_serial_number, cert_digest, signing_time,strPassword = certificate_data(sales_invoice_doc.company)
        
        signature = sign_data(line_xml,strPassword)
        prop_cert_base64 = signed_properties_hash(signing_time, cert_digest, formatted_issuer_name, x509_serial_number)
        
        ubl_extension_string(doc_hash, prop_cert_base64, signature, certificate_base64, signing_time, cert_digest, formatted_issuer_name, x509_serial_number, line_xml)

        compliance_api_call(invoice_number)  #digital signature



    except Exception as e:
        print("ERROR: " + str(e))
        frappe.log_error(title='LHDN invoice call failed', message=get_traceback())



# def signed_properties_hash():
#     try:
#         namespaces = {
#         'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
#         'sig': 'http://www.w3.org/2000/09/xmldsig#',
#         'sac': 'http://uri.etsi.org/01903/v1.3.2#',
#         'ds': 'http://www.w3.org/2000/09/xmldsig#',
#         'xades': 'http://uri.etsi.org/01903/v1.3.2#'
#         }

#         # Replace this with your actual XML file path
#         xml_file_path = frappe.local.site + '/private/files/after_step_4.xml'

#         # Load the XML file
#         updated_invoice_xml = etree.parse(xml_file_path)
#         root = updated_invoice_xml.getroot()

#         # Step 1: Extract the SignedProperties tag using XPath
#         signed_properties = root.xpath(
#             '/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/'
#             'sac:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties',
#             namespaces=namespaces
#         )

#         if not signed_properties:
#             raise ValueError("SignedProperties element not found.")

#         # Get the first matching element
#         signed_properties_xml = signed_properties[0]

#         # Step 2: Linearize the XML block (remove spaces)
#         linearized_xml = etree.tostring(signed_properties_xml, encoding='utf-8', xml_declaration=False).decode('utf-8')
#         linearized_xml = ''.join(linearized_xml.split())  # Remove spaces

#         # Step 3: Hash the property tag using SHA-256
#         sha256_hash = hashlib.sha256(linearized_xml.encode('utf-8')).hexdigest()

#         # Step 4: Encode the hashed property tag using HEX-to-Base64
#         props_digest_base64 = base64.b64encode(bytes.fromhex(sha256_hash)).decode('utf-8')

#         # Step 5: Return the PropsDigest
#         return props_digest_base64

#     except Exception as e:
#         raise Exception("Error in generating signed properties hash: " + str(e))


def removeTags(finalzatcaxml):
    try:
    
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
        canonical_xml = etree.tostring(tag_removed_xml, method="c14n").decode()
        return canonical_xml    
    except Exception as e:
                frappe.throw(" error in canonicalise xml: "+ str(e) )    



def xml_hash():
    try:
        # Read the XML file
        with open(frappe.local.site + "/private/files/create.xml", "rb") as file:
            xml_content = file.read()

        # Parse XML content into an lxml element tree
        root = etree.fromstring(xml_content)

        # Exclude UBLExtensions and Signature elements using XPath (modify according to your XML structure)
        for element in root.xpath('//ext:UBLExtensions | //cac:Signature', namespaces={
            'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
            'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2'
        }):
            element.getparent().remove(element)

        # Canonicalize the XML according to C14N 1.1
        canonical_xml = etree.tostring(root, method="c14n", exclusive=False, with_comments=False)

        # Compute the SHA-256 hash of the canonicalized XML
        sha256_hash = hashlib.sha256(canonical_xml).digest()

        # Convert the digest to base64 encoding
        doc_hash = base64.b64encode(sha256_hash).decode('utf-8')

        return canonical_xml, doc_hash

    except Exception as e:
        frappe.throw(f"Error in xml hash: {str(e)}")



def certificate_data(invoice_company):
    try:
        #Working for fetching specific company certificate
        print("fetching company name",invoice_company)
        company_wise = frappe.get_doc("Lhdn Authorizations", invoice_company)
        print("company_wise",company_wise)
        print("company_wise",company_wise.custom_attach_digital_certificate)
        
        # Get the certificate password
        strPassword = company_wise.get_password('custom_certificate_password')
        print("strPassword",strPassword)
        
        # Path to the attached certificate file
        attached_file = company_wise.custom_attach_digital_certificate
        if not attached_file:
            frappe.throw("No certificate file attached for this company.")

        
        # Fetch the full file path
        file_doc = frappe.get_doc("File", {"file_url": attached_file})
        pfx_path = file_doc.get_full_path()
        print("Certificate file path:", pfx_path)
        
        # Use the dynamic password
        pfx_password = strPassword
        
        
        pem_output_path = frappe.local.site + "/private/files/certificate.pem"
        pem_encryption_password = pfx_password.encode()   
        with open(pfx_path, "rb") as f:
            pfx_data = f.read()
        private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(
            pfx_data, pfx_password.encode(), backend=default_backend()
        )

        with open(pem_output_path, "wb") as pem_file:
            if private_key:
                pem_file.write(private_key.private_bytes(
                    encoding=Encoding.PEM,
                    format=PrivateFormat.PKCS8,  
                    encryption_algorithm=BestAvailableEncryption(pem_encryption_password) 
                ))

            if certificate:
                certificate_base64 = base64.b64encode(certificate.public_bytes(Encoding.DER)).decode("utf-8")
                pem_file.write(certificate.public_bytes(Encoding.PEM))
                x509_issuer_name = formatted_issuer_name = certificate.issuer.rfc4514_string()
                formatted_issuer_name =x509_issuer_name.replace(",", ", ")
                x509_serial_number = certificate.serial_number
                cert_digest = base64.b64encode(certificate.fingerprint(hashes.SHA256())).decode("utf-8")
                # signing_time =  datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
                signing_time = datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')                
            
            if additional_certificates:
                for cert in additional_certificates:
                    pem_file.write(cert.public_bytes(Encoding.PEM))
            return  certificate_base64,formatted_issuer_name,  x509_serial_number ,cert_digest ,signing_time,strPassword
        

    except Exception as e:
        frappe.throw(f"Error loading certificate details: {str(e)}")


def sign_data(line_xml,cert_pass):
    try:
        # print(single_line_ xml1)
        hashdata = line_xml.decode().encode() 
        f = open(frappe.local.site + "/private/files/certificate.pem", "r")
        cert_pem=f.read()
        print("cert_pem",cert_pem)
        if hashdata is None:
            raise ValueError("hashdata cannot be None")
        if cert_pem is None:
            raise ValueError("cert_pem cannot be None")
        cert = load_pem_x509_certificate(cert_pem.encode(), default_backend())
        print("cert:",cert.issuer)
        
        pass_file = cert_pass
        private_key = serialization.load_pem_private_key(
            cert_pem.encode(),
            password=pass_file.encode(),
        )
        
        if private_key is None or not isinstance(private_key, rsa.RSAPrivateKey):
            raise ValueError("The certificate does not contain an RSA private key.")
        
        try:
            signed_data = private_key.sign(
                hashdata,
                padding.PKCS1v15(),
                hashes.SHA256()        
            )
            base64_bytes = base64.b64encode(signed_data)
            base64_string = base64_bytes.decode("ascii")
            # print(f"Encoded string: {base64_string}")
        except Exception as e:
            frappe.throw(f"An error occurred while signing the data.: {str(e)}")
           
        return base64_string
    except Exception as e:
        frappe.throw(f"Error in sign data: {str(e)}")



def signed_properties_hash(signing_time,cert_digest,formatted_issuer_name,x509_serial_number):
        try:

            single_line_xml = f'''<xades:SignedProperties Id="id-xades-signed-props" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#"><xades:SignedSignatureProperties><xades:SigningTime>{signing_time}</xades:SigningTime><xades:SigningCertificate><xades:Cert><xades:CertDigest><ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256" xmlns:ds="http://www.w3.org/2000/09/xmldsig#"></ds:DigestMethod><ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{cert_digest}</ds:DigestValue></xades:CertDigest><xades:IssuerSerial><ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{formatted_issuer_name}</ds:X509IssuerName><ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{x509_serial_number}</ds:X509SerialNumber></xades:IssuerSerial></xades:Cert></xades:SigningCertificate></xades:SignedSignatureProperties></xades:SignedProperties>'''
            prop_cert_hash = hashlib.sha256(single_line_xml.encode('utf-8')).digest()
            prop_cert_base64 = base64.b64encode(prop_cert_hash).decode('utf-8')
            # print(f"SHA-256 Hash in Base64 (propCert): {prop_cert_base64}")
            return prop_cert_base64
        except Exception as e:
            frappe.throw(f"Error signed properties hash: {str(e)}")


def ubl_extension_string(doc_hash,prop_cert_base64,signature,certificate_base64,signing_time,cert_digest,formatted_issuer_name,x509_serial_number,line_xml):
        try:
                inv_xml_string = f"""<ext:UBLExtensions>
                        <ext:UBLExtension>
                            <ext:ExtensionURI>urn:oasis:names:specification:ubl:dsig:enveloped:xades</ext:ExtensionURI>
                            <ext:ExtensionContent>
                                <sig:UBLDocumentSignatures xmlns:sac="urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2"
                                     xmlns:sbc="urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2"
                                     xmlns:sig="urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2">
                                    <sac:SignatureInformation>
                                        <cbc:ID>urn:oasis:names:specification:ubl:signature:1</cbc:ID>
                                        <sbc:ReferencedSignatureID>urn:oasis:names:specification:ubl:signature:Invoice</sbc:ReferencedSignatureID>
                                        <ds:Signature xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Id="signature">
                                            <ds:SignedInfo>
                                                <ds:CanonicalizationMethod Algorithm="http://www.w3.org/2006/12/xml-c14n11"></ds:CanonicalizationMethod>
                                                <ds:SignatureMethod Algorithm="http://www.w3.org/2001/04/xmldsig-more#rsa-sha256"></ds:SignatureMethod>
                                                <ds:Reference Id="id-doc-signed-data" URI="">
                                                    <ds:Transforms>
                                                        <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116">
                                                            <ds:XPath>not(//ancestor-or-self::ext:UBLExtensions)</ds:XPath>
                                                        </ds:Transform>
                                                        <ds:Transform Algorithm="http://www.w3.org/TR/1999/REC-xpath-19991116">
                                                            <ds:XPath>not(//ancestor-or-self::cac:Signature)</ds:XPath>
                                                        </ds:Transform>
                                                        <ds:Transform Algorithm="http://www.w3.org/2006/12/xml-c14n11"></ds:Transform>
                                                    </ds:Transforms>
                                                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>
                                                    <ds:DigestValue>{doc_hash}</ds:DigestValue>
                                                </ds:Reference>
                                                <ds:Reference Type="http://www.w3.org/2000/09/xmldsig#SignatureProperties" URI="#id-xades-signed-props">
                                                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>
                                                    <ds:DigestValue>{prop_cert_base64}</ds:DigestValue>
                                                </ds:Reference>
                                            </ds:SignedInfo>
                                            <ds:SignatureValue>{signature}</ds:SignatureValue>
                                            <ds:KeyInfo>
                                                <ds:X509Data>
                                                    <ds:X509Certificate>{certificate_base64}</ds:X509Certificate>
                                                </ds:X509Data>
                                            </ds:KeyInfo>
                                            <ds:Object>
                                                <xades:QualifyingProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Target="signature">
                                                    <xades:SignedProperties Id="id-xades-signed-props">
                                                        <xades:SignedSignatureProperties>
                                                            <xades:SigningTime>{signing_time}</xades:SigningTime>
                                                            <xades:SigningCertificate>
                                                                <xades:Cert>
                                                                    <xades:CertDigest>
                                                                        <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"></ds:DigestMethod>
                                                                        <ds:DigestValue>{cert_digest}</ds:DigestValue>
                                                                    </xades:CertDigest>
                                                                    <xades:IssuerSerial>
                                                                        <ds:X509IssuerName>{formatted_issuer_name}</ds:X509IssuerName>
                                                                        <ds:X509SerialNumber>{x509_serial_number}</ds:X509SerialNumber>
                                                                    </xades:IssuerSerial>
                                                                </xades:Cert>
                                                            </xades:SigningCertificate>
                                                        </xades:SignedSignatureProperties>
                                                    </xades:SignedProperties>
                                                </xades:QualifyingProperties>
                                            </ds:Object>
                                        </ds:Signature>
                                    </sac:SignatureInformation>
                                </sig:UBLDocumentSignatures>
                            </ext:ExtensionContent>
                        </ext:UBLExtension>
                    </ext:UBLExtensions>"""
                inv_xml_string_single_line = inv_xml_string.replace("\n", "").replace("  ", "").replace("> <", "><")
                string=line_xml.decode()
                if isinstance(string, str) and isinstance(inv_xml_string_single_line, str):
                
                    insert_position = string.find(">") + 1
                    result = string[:insert_position] + inv_xml_string_single_line + string[insert_position:]

                
                signature_string = """<cac:Signature><cbc:ID>urn:oasis:names:specification:ubl:signature:Invoice</cbc:ID><cbc:SignatureMethod>urn:oasis:names:specification:ubl:dsig:enveloped:xades</cbc:SignatureMethod></cac:Signature>"""
                insert_position = result.find("<cac:AccountingSupplierParty>")
                if insert_position != -1:  
                    
                    result_final = result[:insert_position] + signature_string + result[insert_position:]
                    # print(result_final)

                    output_path = frappe.local.site + "/private/files/output.xml"
                    with open(output_path, "w") as file:
                        file.write(result_final)
                    
                    
                    # frappe.throw("The modified XML has been saved to 'signedxml_for_submit.xml'.")
                else:
                    frappe.throw("The element <cac:AccountingSupplierParty> was not found in the XML string.")
        except Exception as e:
            frappe.throw(f"Error ubl extension string: {str(e)}")


def getInvoiceHash(canonicalized_xml):
        try:
            print("signature hash")
       
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


def get_invoice_version():
    settings =  frappe.get_doc('Lhdn Settings')
    invoice_version = settings.invoice_version
    return invoice_version


def remove_api_from_url(url):
    settings =  frappe.get_doc('Lhdn Settings')
    api_environment = settings.select
    
    if api_environment == "Sandbox":
        parsed_url = urlparse(url)
        new_netloc = parsed_url.netloc.replace('-api', '')
        new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
        return new_url
    
    if api_environment == "Production":
        parsed_url = urlparse(url)
        new_netloc = parsed_url.netloc.replace('api.', '')
        new_url = urlunparse(parsed_url._replace(netloc=new_netloc))
        return new_url

        

def compliance_api_call(invoice_number):
    try:
        
        sale_doc = frappe.get_doc("Sales Invoice", invoice_number)
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


def make_qr_code_url(uuid,long_id):
        qr_code_url = get_API_url(base_url=f"/{uuid}/share/{long_id}")
    
        return qr_code_url


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


 
