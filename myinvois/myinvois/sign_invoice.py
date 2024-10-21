from lxml import etree
import hashlib
import base64
import lxml.etree as MyTree
from datetime import datetime
import xml.etree.ElementTree as ET
import frappe
import os
from datetime import datetime, timezone, timedelta

from myinvois.myinvois.createxml import xml_tags,salesinvoice_data,set_total_amounts,set_tax_type_main_form,invoice_Typecode_Simplified,invoice_Typecode_Standard,doc_Reference,additional_Reference ,company_Data,customer_Data,delivery_And_PaymentMeans,tax_Data,item_data,xml_structuring,invoice_Typecode_Compliance,delivery_And_PaymentMeans_for_Compliance,doc_Reference_compliance,get_tax_total_from_items
import pyqrcode
import binascii

from cryptography import x509
from cryptography.hazmat._oid import NameOID
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.bindings._rust import ObjectIdentifier
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.asymmetric import utils


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
from urllib.parse import urlparse, urlunparse



import frappe
import pyqrcode

from datetime import datetime, timedelta
import requests
import frappe


import qrcode
import base64
from io import BytesIO

import os
import base64
from OpenSSL import crypto


from lxml import etree
import hashlib
import base64
import datetime
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import rsa, padding
from cryptography.x509 import load_pem_x509_certificate
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.serialization import pkcs12, Encoding, BestAvailableEncryption, PrivateFormat
from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import hashes, serialization
import frappe       
import requests


@frappe.whitelist()
def gen_qrcode(text):
    data = pyqrcode.create(text)

    return f'data:image/png;base64,{data.png_as_base64_str(scale=2)}'


def sign_document_digest(encoded_hash):

        


    # Step 4

    # Get the current script path
    current_path = os.path.dirname(__file__)

    # Path to the .p12 file
    p12_file_path = os.path.join(current_path, "test.p12")  # include your softcert here
    p12_password = b"My8}XPyP"  # include your softcert password here (note: use byte string)

    # Check if the file exists and is readable
    if not os.path.exists(p12_file_path):
        raise FileNotFoundError(f'The .p12 file does not exist: {p12_file_path}')
    if not os.access(p12_file_path, os.R_OK):
        raise PermissionError(f'The .p12 file is not readable: {p12_file_path}')

    # Load the .p12 file
    with open(p12_file_path, 'rb') as p12_file:
        p12_content = p12_file.read()

    # Load the PKCS#12 file
    private_key, certificate, additional_certificates = pkcs12.load_key_and_certificates(p12_content, p12_password)

    print("private key",private_key)
    print("certi",certificate)
    print("additon",additional_certificates)

    # Extract issuer name and serial number from the certificate
    issuer = certificate.issuer
    serial_number = certificate.serial_number

    print(f"Issuer: {issuer}")
    print(f"Serial Number: {serial_number}")

    # Extract human-readable issuer name
    issuer_name = ', '.join([f"{name.oid._name}={name.value}" for name in issuer])
    print(f"Issuer Name: {issuer_name}")

    # Data to sign
    # data = b'JDU5huARfDgxsGqgw47wUQpD8VR7L4t7C+6lUFF2DPU='
    data = encoded_hash.encode('utf-8')
    print("data",data)

    # Sign the data using RSA-SHA256
    # signature = private_key.sign(
    #     data,
    #     padding.PKCS1v15(),
    #     hashes.SHA256()
    # ) 
    
    # Step 1: Convert encoded hash (hex/base64 string) back to bytes if necessary
    canonical_xml_hash = base64.b64decode(encoded_hash)  # Assuming `encoded_hash` is Base64-encoded hash

    print("canon",canonical_xml_hash)

    signature = private_key.sign(
        canonical_xml_hash,               # Signing the hash (not the raw XML)
        padding.PKCS1v15(),               # RSA-PKCS1v15 padding scheme
        utils.Prehashed(hashes.SHA256())  # Indicate that the data is pre-hashed
    )

    print("property sig",signature)

    # Output the signature in base64 format
    signature_base64 = base64.b64encode(signature).decode('utf-8')
    print(f'Signature: {signature_base64}')


    # Step 5: Generate the SHA-256 hash of the signing certificate
    digest = hashes.Hash(hashes.SHA256())
    digest.update(certificate.public_bytes(encoding=serialization.Encoding.DER))  # Use DER format for hashing
    certificate_hash = digest.finalize()

    # Encode the certificate hash using Base64
    certificate_hash_base64 = base64.b64encode(certificate_hash).decode('utf-8')
    print(f"SHA-256 Certificate Hash in Base64: {certificate_hash_base64}")

    # Output the certificate in PEM format (if needed)
    
    certificate_pem = certificate.public_bytes(encoding=serialization.Encoding.PEM).decode('utf-8')
    print(f'Certificate: {certificate_pem}')

    # extract_certificate_details(certificate_content)

    


    # # If needed, output the certificate
    # # certificate_pem = certificate.public_bytes().decode('utf-8')
    # certificate_pem = certificate.public_bytes(encoding=serialization.Encoding.PEM).decode('utf-8')
    # print(f'Certificate: {certificate_pem}')

    return signature_base64, certificate_hash_base64,certificate_pem, issuer_name, serial_number

# def extract_certificate_details(company_abbr):
def extract_certificate_details(certificate_content):

    try:
        # Retrieve the company document based on the provided abbreviation
        # company_name = frappe.db.get_value("Company", {"abbr": company_abbr}, "name")
        # if not company_name:
        #     frappe.throw(f"Company with abbreviation {company_abbr} not found.")
        
        # company_doc = frappe.get_doc('Company', company_name)
        # certificate_data_str = company_doc.get("custom_certificate")

        # if not certificate_data_str:
        #     frappe.throw(f"No certificate data found for company {company_name}")
        
        # # The certificate content is directly stored as a string
        # certificate_content = certificate_data_str.strip()

        # if not certificate_content:
        #     frappe.throw(f"No valid certificate content found for company {company_name}")

        # Format the certificate string to PEM format if not already in correct PEM format
        formatted_certificate = "-----BEGIN CERTIFICATE-----\n"
        formatted_certificate += "\n".join(certificate_content[i:i+64] for i in range(0, len(certificate_content), 64))
        formatted_certificate += "\n-----END CERTIFICATE-----\n"
        
        # Load the certificate using cryptography
        certificate_bytes = formatted_certificate.encode('utf-8')
        cert = x509.load_pem_x509_certificate(certificate_bytes, default_backend())
        
        # Extract the issuer name and serial number
        formatted_issuer_name = cert.issuer.rfc4514_string()
        issuer_name = ", ".join([x.strip() for x in formatted_issuer_name.split(',')])
        serial_number = cert.serial_number

        print("generated issuer name",issuer_name)
        print("serial",serial_number)

        return issuer_name, serial_number

    except Exception as e:
        frappe.throw("Error in extracting certificate details: " + str(e))

# def signxml_modify(company_abbr):
def signxml_modify(certificate_hash_base64, issuer_name, serial_number):
                try:
                    # company_name = frappe.db.get_value("Company", {"abbr": company_abbr}, "name")
                    # company_doc = frappe.get_doc('Company', company_name)
                    # encoded_certificate_hash= certificate_hash(company_abbr)
                    # issuer_name, serial_number = extract_certificate_details(company_abbr)
                    
                    
                    
                    original_invoice_xml = etree.parse(frappe.local.site + '/private/files/finalzatcaxml.xml')
                    root = original_invoice_xml.getroot()
                    namespaces = {
                    'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
                    'sig': 'urn:oasis:names:specification:ubl:schema:xsd:CommonSignatureComponents-2',
                    'sac':"urn:oasis:names:specification:ubl:schema:xsd:SignatureAggregateComponents-2", 
                    'xades': 'http://uri.etsi.org/01903/v1.3.2#',
                    'ds': 'http://www.w3.org/2000/09/xmldsig#'}
                    ubl_extensions_xpath = "//*[local-name()='Invoice']//*[local-name()='UBLExtensions']"
                    # qr_xpath = "//*[local-name()='AdditionalDocumentReference'][cbc:ID[normalize-space(text()) = 'QR']]"
                    signature_xpath = "//*[local-name()='Invoice']//*[local-name()='Signature']"
                    xpath_dv = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties/xades:SignedSignatureProperties/xades:SigningCertificate/xades:Cert/xades:CertDigest/ds:DigestValue")
                    xpath_signTime = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties/xades:SignedSignatureProperties/xades:SigningTime")
                    xpath_issuerName = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties/xades:SignedSignatureProperties/xades:SigningCertificate/xades:Cert/xades:IssuerSerial/ds:X509IssuerName")
                    xpath_serialNum = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties//xades:SignedSignatureProperties/xades:SigningCertificate/xades:Cert/xades:IssuerSerial/ds:X509SerialNumber")
                    element_dv = root.find(xpath_dv, namespaces)
                    element_st = root.find(xpath_signTime, namespaces)
                    element_in = root.find(xpath_issuerName, namespaces)
                    element_sn = root.find(xpath_serialNum, namespaces)
                    element_dv.text = (certificate_hash_base64)   #encoded_certificate_hash replace with mine variable
                    element_st.text =  datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
                    signing_time =element_st.text
                    element_in.text = issuer_name
                    element_sn.text = str(serial_number)
                    with open(frappe.local.site + "/private/files/after_step_4.xml", 'wb') as file:
                        original_invoice_xml.write(file,encoding='utf-8',xml_declaration=True,)
                    return namespaces ,signing_time
                except Exception as e:
                    frappe.throw(" error in modification of xml sign part: "+ str(e) )




###################################For testing###########

def signed_properties_hash():
    try:
        namespaces = {
        'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
        'sig': 'http://www.w3.org/2000/09/xmldsig#',
        'sac': 'http://uri.etsi.org/01903/v1.3.2#',
        'ds': 'http://www.w3.org/2000/09/xmldsig#',
        'xades': 'http://uri.etsi.org/01903/v1.3.2#'
        }

        # Replace this with your actual XML file path
        xml_file_path = frappe.local.site + '/private/files/after_step_4.xml'

        # Load the XML file
        updated_invoice_xml = etree.parse(xml_file_path)
        root = updated_invoice_xml.getroot()

        # Step 1: Extract the SignedProperties tag using XPath
        signed_properties = root.xpath(
            '/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/'
            'sac:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties',
            namespaces=namespaces
        )

        if not signed_properties:
            raise ValueError("SignedProperties element not found.")

        # Get the first matching element
        signed_properties_xml = signed_properties[0]

        # Step 2: Linearize the XML block (remove spaces)
        linearized_xml = etree.tostring(signed_properties_xml, encoding='utf-8', xml_declaration=False).decode('utf-8')
        linearized_xml = ''.join(linearized_xml.split())  # Remove spaces

        # Step 3: Hash the property tag using SHA-256
        sha256_hash = hashlib.sha256(linearized_xml.encode('utf-8')).hexdigest()

        # Step 4: Encode the hashed property tag using HEX-to-Base64
        props_digest_base64 = base64.b64encode(bytes.fromhex(sha256_hash)).decode('utf-8')

        # Step 5: Return the PropsDigest
        return props_digest_base64

    except Exception as e:
        raise Exception("Error in generating signed properties hash: " + str(e))


#############################33testing#3
import hashlib
import base64
from lxml import etree

import hashlib
import base64
from lxml import etree

# def signed_properties_hash():
#     """
#     Generates the PropsDigest by extracting the SignedProperties tag from the XML file
#     located at /private/files/after_step_4.xml, canonicalizing it, hashing it using SHA-256,
#     and encoding it in Base64.
    
#     :return: Base64 encoded hash of the SignedProperties.
#     """
    
#     # Define the fixed file path
# # Define the file path relative to the site directory
#     file_path = frappe.get_site_path('private', 'files', 'after_step_4.xml')
        
#     # Namespaces used in the XML for XPath lookup
#     namespaces = {
#     'ext': 'urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2',
#     'sig': 'urn:oasis:names:specification:ubl:schema:xsd:SignatureBasicComponents-2',
#     'sac': 'http://www.w3.org/2000/09/xmldsig#',
#     'ds': 'http://www.w3.org/2000/09/xmldsig#',
#     'xades': 'http://uri.etsi.org/01903/v1.3.2#'
# }
    

#     try:
#         # Load the XML file from the fixed file path
#         with open(file_path, 'rb') as f:
#             xml_content = f.read()
#             print("xml_content",xml_content)

#         # Parse the XML content using lxml
#         root = etree.fromstring(xml_content)
#     except Exception as e:
#         raise ValueError(f"Error reading or parsing XML file: {str(e)}")
    

#     ubl_extensions = root.xpath('/Invoice/ext:UBLExtensions', namespaces=namespaces)
#     ubl_extension = root.xpath('/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent', namespaces=namespaces)

#     # Extract the SignedProperties tag using XPath
#     signed_properties = root.xpath(
#         '/Invoice/ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sig:SignatureInformation/ds:Signature/ds:Object/xades:QualifyingProperties/xades:SignedProperties',namespaces=namespaces
#     )
    
#     if not signed_properties:
#         raise ValueError("SignedProperties tag not found in the XML.")
    
#     # Convert the SignedProperties element to a string (linearize and canonicalize)
#     signed_properties_str = etree.tostring(signed_properties[0], method='c14n', exclusive=True, with_comments=False)
    
#     # Hash the canonicalized SignedProperties string using SHA-256
#     sha256_hash = hashlib.sha256(signed_properties_str).digest()
#     print("sha256_hash",sha256_hash)
    
#     # Encode the hashed value using Base64
#     props_digest = base64.b64encode(sha256_hash).decode('utf-8')
#     print("props_digest",props_digest)
    
#     return props_digest


# # Example usage: Call the function to generate the PropsDigest
# props_digest_value = generate_signed_properties_hash()
# print(f"PropsDigest: {props_digest_value}")





##########  original#############



def generate_Signed_Properties_Hash(signing_time,issuer_name,serial_number,certificate_hash_base64):
            try:
                print("signing_time",signing_time)
                print("certificate_hash",certificate_hash_base64)
                print("issuer_name",issuer_name)
                print("serial_number",serial_number)
               

                # xml_string = '''<xades:SignedProperties Id="id-xades-signed-props">
                #                     <xades:SignedSignatureProperties>
                #                         <xades:SigningTime>{signing_time}</xades:SigningTime>
                #                         <xades:SigningCertificate>
                #                             <xades:Cert>
                #                                 <xades:CertDigest>
                #                                     <ds:DigestMethod xmlns:ds="http://www.w3.org/2000/09/xmldsig#" Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>
                #                                     <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{certificate_hash}</ds:DigestValue>
                #                                 </xades:CertDigest>
                #                                 <xades:IssuerSerial>
                #                                     <ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{issuer_name}</ds:X509IssuerName>
                #                                     <ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{serial_number}</ds:X509SerialNumber>
                #                                 </xades:IssuerSerial>
                #                             </xades:Cert>
                #                         </xades:SigningCertificate>
                #                     </xades:SignedSignatureProperties>
                #                 </xades:SignedProperties>'''
                
                xml_string = '''<xades:SignedProperties Id="id-xades-signed-props" xmlns:xades="http://uri.etsi.org/01903/v1.3.2#">
                                    <xades:SignedSignatureProperties>
                                        <xades:SigningTime>{signing_time}</xades:SigningTime>
                                        <xades:SigningCertificate>
                                            <xades:Cert>
                                                <xades:CertDigest>
                                                    <ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256" xmlns:ds="http://www.w3.org/2000/09/xmldsig#">
                                                    <ds:DigestValue xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{certificate_hash_base64}</ds:DigestValue>
                                                </xades:CertDigest>
                                                <xades:IssuerSerial>
                                                    <ds:X509IssuerName xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{issuer_name}</ds:X509IssuerName>
                                                    <ds:X509SerialNumber xmlns:ds="http://www.w3.org/2000/09/xmldsig#">{serial_number}</ds:X509SerialNumber>
                                                </xades:IssuerSerial>
                                            </xades:Cert>
                                        </xades:SigningCertificate>
                                    </xades:SignedSignatureProperties>
                                </xades:SignedProperties>'''
                
                xml_string_rendered = xml_string.format(signing_time=signing_time, certificate_hash_base64=certificate_hash_base64, issuer_name=issuer_name, serial_number=str(serial_number))
                utf8_bytes = xml_string_rendered.encode('utf-8')
                hash_object = hashlib.sha256(utf8_bytes)
                hex_sha256 = hash_object.hexdigest()
                print("Properties hash 256",hex_sha256)
                signed_properties_base64=  base64.b64encode(hex_sha256.encode('utf-8')).decode('utf-8')
                print("Signed properties base 64",signed_properties_base64)
                return signed_properties_base64
            except Exception as e:
                    frappe.throw(" error in generating signed properties hash: "+ str(e) )


# def populate_The_UBL_Extensions_Output(encoded_signature, namespaces, signed_properties_base64, encoded_hash, company_abbr):
def populate_The_UBL_Extensions_Output(encoded_signature, namespaces, signed_properties_base64, encoded_hash,certificate_pem):
    
    try:
        # Load the XML file
        updated_invoice_xml = etree.parse(frappe.local.site + '/private/files/after_step_4.xml')
        root3 = updated_invoice_xml.getroot()

        # # Retrieve the company document based on the provided abbreviation
        # company_name = frappe.db.get_value("Company", {"abbr": company_abbr}, "name")
        # if not company_name:
        #     frappe.throw(f"Company with abbreviation {company_abbr} not found.")
        
        # company_doc = frappe.get_doc('Company', company_name)
        # certificate_data_str = company_doc.get("custom_certificate")

        # if not certificate_data_str:
        #     frappe.throw(f"No certificate data found for company {company_name}")
        
        
        # Directly use the certificate data
        print("before removing begin and end certificate",certificate_pem)
        content = certificate_pem.replace("-----BEGIN CERTIFICATE-----", "").replace("-----END CERTIFICATE-----", "").strip()
        
        print("After removing ",content)

        # if not content:
        #     frappe.throw(f"No valid certificate content found for company {company_name}")
    
    
        # Define the XPaths for the elements to update
        xpath_signvalue = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:SignatureValue")
        xpath_x509certi = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:KeyInfo/ds:X509Data/ds:X509Certificate")
        # xpath_digvalue = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:SignedInfo/ds:Reference[@URI='#xadesSignedProperties']/ds:DigestValue")
        xpath_digvalue = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:SignedInfo/ds:Reference[@URI='#id-xades-signed-props']/ds:DigestValue")

        # xpath_digvalue2 = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:SignedInfo/ds:Reference[@Id='invoiceSignedData']/ds:DigestValue")
        xpath_digvalue2 = ("ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/sig:UBLDocumentSignatures/sac:SignatureInformation/ds:Signature/ds:SignedInfo/ds:Reference[@Id='id-doc-signed-data']/ds:DigestValue")


        # Locate elements to update in the XML
        signValue6 = root3.find(xpath_signvalue, namespaces)
        x509Certificate6 = root3.find(xpath_x509certi, namespaces)
        digestvalue6 = root3.find(xpath_digvalue, namespaces)
        digestvalue6_2 = root3.find(xpath_digvalue2, namespaces)

        
        signValue6.text = encoded_signature
        x509Certificate6.text = content
        digestvalue6.text = signed_properties_base64
        digestvalue6_2.text = encoded_hash

        
        with open(frappe.local.site + "/private/files/final_xml_after_sign.xml", 'wb') as file:
            updated_invoice_xml.write(file, encoding='utf-8', xml_declaration=True)

    except Exception as e:
        frappe.throw("Error in populating UBL extension output: " + str(e))


def structuring_signedxml():
                try:
                    with open(frappe.local.site + '/private/files/final_xml_after_sign.xml', 'r') as file:
                        xml_content = file.readlines()
                    indentations = {
                        29: ['<xades:QualifyingProperties xmlns:xades="http://uri.etsi.org/01903/v1.3.2#" Target="signature">','</xades:QualifyingProperties>'],
                        33: ['<xades:SignedProperties Id="id-xades-signed-props">', '</xades:SignedProperties>'],
                        37: ['<xades:SignedSignatureProperties>','</xades:SignedSignatureProperties>'],
                        41: ['<xades:SigningTime>', '<xades:SigningCertificate>','</xades:SigningCertificate>'],
                        45: ['<xades:Cert>','</xades:Cert>'],
                        49: ['<xades:CertDigest>', '<xades:IssuerSerial>', '</xades:CertDigest>', '</xades:IssuerSerial>'],
                        53: ['<ds:DigestMethod Algorithm="http://www.w3.org/2001/04/xmlenc#sha256"/>', '<ds:DigestValue>', '<ds:X509IssuerName>', '<ds:X509SerialNumber>']
                    }
                    def adjust_indentation(line):
                        for col, tags in indentations.items():
                            for tag in tags:
                                if line.strip().startswith(tag):
                                    return ' ' * (col - 1) + line.lstrip()
                        return line
                    adjusted_xml_content = [adjust_indentation(line) for line in xml_content]
                    with open(frappe.local.site + '/private/files/final_xml_after_indent.xml', 'w') as file:
                        file.writelines(adjusted_xml_content)
                    signed_xmlfile_name = frappe.local.site + '/private/files/final_xml_after_indent.xml'
                    return signed_xmlfile_name
                except Exception as e:
                    frappe.throw(" error in structuring signed xml: "+ str(e) )
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



def xml_sha256_hash(signed_xmlfile_name):
    try:
        with open(signed_xmlfile_name, "r") as file:
            xml = file.read().lstrip()
            # Encode the XML content into bytes
            xml_bytes = xml.encode("utf-8")
            # Compute the SHA-256 hash
            sha256_hash = hashlib.sha256(xml_bytes).hexdigest()
            return sha256_hash
    except Exception as e:
        frappe.msgprint("Error in XML SHA-256 hash: " + str(e))

    
def xml_base64_Decode(signed_xmlfile_name):
                    try:
                        with open(signed_xmlfile_name, "r") as file:
                                        xml = file.read().lstrip()
                                        base64_encoded = base64.b64encode(xml.encode("utf-8"))
                                        base64_decoded = base64_encoded.decode("utf-8")
                                        return base64_decoded
                    except Exception as e:
                        frappe.msgprint("Error in xml base64:  " + str(e) )




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
        # print("hash_hex", hash_hex)

        # Base64 encode the canonicalized XML
        base64_encoded_xml = base64.b64encode(canonicalized_xml.encode()).decode('utf-8')
        # print("base64_encoded_xml", base64_encoded_xml)

        return hash_hex, base64_encoded_xml
    except Exception as e:
        frappe.throw("Error in Invoice hash of xml: " + str(e))


#####################################   New Logic #########3
import hashlib
import base64
from lxml import etree
from io import BytesIO

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


# def xml_hash():
#     try:
#         with open(frappe.local.site + "/private/files/create.xml", "rb") as file:
#             xml_content = file.read()
#         root = etree.fromstring(xml_content)
#         line_xml = etree.tostring(root, pretty_print=False, encoding='UTF-8')
#         sha256_hash = hashlib.sha256(line_xml).digest()  
#         doc_hash = base64.b64encode(sha256_hash).decode('utf-8')
#         return line_xml,doc_hash
#     except Exception as e:
#             frappe.throw(f"Error in xml hash: {str(e)}")


def certificate_data():
    try:

        # settings = frappe.get_doc('LHDN Malaysia Setting')
        # attached_file = settings.certificate_file

        # if not attached_file:
        #     frappe.throw("No PFX file attached in the settings.")
        # file_doc = frappe.get_doc("File", {"file_url": attached_file})
        # pfx_path = file_doc.get_full_path()

        current_path = os.path.dirname(__file__)

        # Path to the .p12 file
        p12_file_path = os.path.join(current_path, "test.p12")  # include your softcert here
        p12_password = b"My8}XPyP"  # include your softcert password here (note: use byte string)

        pfx_path = p12_file_path
        
        pfx_password = "My8}XPyP"
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
            return  certificate_base64,formatted_issuer_name,  x509_serial_number ,cert_digest ,signing_time
        

    except Exception as e:
        frappe.throw(f"Error loading certificate details: {str(e)}")



def bytes_to_base64_string(value: bytes) -> str:   
   return base64.b64encode(value).decode('ASCII')

def sign_data(line_xml):
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
        # settings = frappe.get_doc('LHDN Malaysia Setting')
        # pass_file=settings.pfx_cert_password
        pass_file = "My8}XPyP"
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

###########################################  End Of New Logic################3

def getInvoiceHash(canonicalized_xml):
        try:
            # print("enter in hash method")
            # print("Nexxxxxxxxxxxxxxxxx xml",canonicalized_xml)
            print("signature hash")
       
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





# @frappe.whitelist()
# def get_access_token(company_name):
#     # Fetch the credentials from the custom doctype
#     credentials = frappe.get_doc("Lhdn Authorizations", company_name)
#     client_id = credentials.client_id
#     client_secret = credentials.get_password(fieldname='client_secret_key', raise_exception=False)   

#     # # Check if token is already available and not expired
#     if credentials.access_token and credentials.token_expiry:
#         print("checking enter in first if")
#         token_expiry = datetime.strptime(str(credentials.token_expiry), "%Y-%m-%d %H:%M:%S")
#         print("token_expiry",token_expiry)
#         if datetime.now() < token_expiry:
#             print("second if")
#             return credentials.access_token

#     # # If token is expired or not available, request a new one
#     # make url dynamic
#     # get_API_url(base_url="/connect/token")
#     response = requests.request("POST", url= get_API_url(base_url="/connect/token"), data={
#         "client_id": client_id,
#         "client_secret": client_secret,
#         "grant_type": "client_credentials",
#         "scope": "InvoicingAPI"
#     })

#     # response = requests.post("https://{base_url}/connect/token", data={
#     #     "client_id": client_id,
#     #     "client_secret": client_secret,
#     #     "grant_type": "client_credentials",
#     #     "scope": "InvoicingAPI"
#     # })
#     print("response",response)

#     if response.status_code == 200:
#         data = response.json()
#         access_token = data["access_token"]
#         expires_in = data["expires_in"]
#         token_expiry = datetime.now() + timedelta(seconds=expires_in)

#         # Store the new token and expiry in the custom doctype
#         credentials.access_token = access_token
#         credentials.token_expiry = token_expiry.strftime("%Y-%m-%d %H:%M:%S")
#         credentials.save()

#         return access_token
#     else:
#         frappe.throw("Failed to fetch access token")

from datetime import datetime, timedelta
import requests
import frappe

@frappe.whitelist()
def get_access_token(company_name):
    # Fetch the credentials from the custom doctype
    credentials = frappe.get_doc("Lhdn Authorizations", company_name)
    client_id = credentials.client_id
    client_secret = credentials.get_password(fieldname='client_secret_key', raise_exception=False)   

    # Check if token is already available and not expired
    if credentials.access_token and credentials.token_expiry:
        print("checking enter in first if")
        token_expiry = datetime.strptime(str(credentials.token_expiry), "%Y-%m-%d %H:%M:%S")
        print("token_expiry", token_expiry)
        if datetime.now() < token_expiry:
            print("second if")
            return credentials.access_token

    # If token is expired or not available, request a new one
    response = requests.request("POST", url=get_API_url(base_url="/connect/token"), data={
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "client_credentials",
        "scope": "InvoicingAPI"
    })

    print("response", response)

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


def get_invoice_version():
    settings =  frappe.get_doc('Lhdn Settings')
    invoice_version = settings.invoice_version
    return invoice_version


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

def remove_api_from_url(url):
    parsed_url = urlparse(url)
    new_netloc = parsed_url.netloc.replace('-api', '')
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
                    else:
                        frappe.throw("Token for company {} not found".format(company_name))
                    try:
                        # frappe.throw("inside compliance api call2")
                        # response = requests.request("POST", url=get_API_url(base_url="compliance/invoices"), headers=headers, data=payload)
                        
                        #Submit Documents Api
                        #Posting Invoice to Lhdn Portal
                        
                        frappe.publish_progress(25, title='Progressing', description='wait sometime')

                        ## First Api
                        api_url = get_API_url(base_url=f"/api/{invoice_version}/documentsubmissions")
                        response = requests.post(api_url, headers=headers, data=payload_json)

                        response_text = response.text
                        response_status_code= response.status_code

                        print("checking reposnse",response_text)
                        print("response.status_code",response.status_code)


                        # frappe.msgprint(f"API Status: {response_status}\nResponse: {response_text}")
                        # frappe.msgprint(f"API Status: {response_status}\nResponse:\n{response_text}")

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
                                #https://{{apiBaseUrl}}/api/v1.0/documents/51W5N1C6SCZ9AHBK39YQF03J10/details
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
                                    
                                    
                                    # qr_code_url = make_qr_code_url(uuid,doc_long_id)
                                    
                                    # sale_doc.db_set("custom_lhdn_status", doc_status)
                                    # sale_doc.db_set("custom_qr_code_link",qr_code_url)  

                                    
                                        frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Message : QR Code Url Updated<br>Response: {response_text}")

                                else:

                                    print("enter in else validation")
                                    doc_status = "InProgress"
                                    sale_doc.db_set("custom_lhdn_status", doc_status)  

                                    frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Response: <br>{response_text}")

                                    # print("enter in else validaiton")
                                    # # validation_results = status_data.get("validationResults", [])
                                    # # uuid = accepted_documents[0].get("uuid")
                                    # validation_results=status_data.get("validation_results")
                                    # frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Response: {validation_results}")

                            
                            if rejected_documents:
                                frappe.publish_progress(100, title='Progressing', description='wait sometime')


                                print("enter in rejected doc")
                                doc_status = "Rejected"
                                sale_doc.db_set("custom_lhdn_status", doc_status)  

                                frappe.msgprint(f"Document Status: {doc_status}<br>Response: <br>{response_text}")

                                # frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Response: {validation_results}")

                                   
                               
                            #frappe.msgprint(f"API Status Code: {response_status_code}<br>Document Status: {doc_status}<br>Response: {response_text}")

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


def make_qr_code_url(uuid,long_id):
        qr_code_url = get_API_url(base_url=f"/{uuid}/share/{long_id}")
    
        return qr_code_url

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
                        
                        myinvois_Call(invoice_number,1)
                        
                    except Exception as e:
                        frappe.throw("Error in background call:  " + str(e) )


# working on b2b
#compliance_type is invoice_type
 
@frappe.whitelist(allow_guest=True)
def myinvois_Call(invoice_number, compliance_type):
    try:
        print("enter in myinvoice call method")

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

        # invoice = additional_Reference(invoice) Adding cac:signature

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


        # #Convert XML to pretty string
        pretty_xml_string = xml_structuring(invoice, sales_invoice_doc)

        # ###########################
        # #Starting code with new git
        # ##########################
        with open(frappe.local.site + "/private/files/create.xml", 'r') as file:
                                    file_content = file.read()

        print("file content",file_content)
        # print("file_content",file_content)
        
        tag_removed_xml = removeTags(file_content)
        print("tag_removed_xml",tag_removed_xml)    
        


        canonicalized_xml = canonicalize_xml(tag_removed_xml)

        # hash_hex, base64_encoded_xml = getDoceHash_base64(canonicalized_xml)  #this method generating hash and base64 seperately using canonical xml
        # print("hash1",hash_hex)
        # compliance_api_call(encoded_hash, signed_xmlfile_name)

        hash1, encoded_hash = getInvoiceHash(canonicalized_xml)  #this method first convert canonical to hash hex then base64
        line_xml, doc_hash = xml_hash()
        print("line_xml",line_xml)
        print("doc_hash",doc_hash)
        certificate_base64, formatted_issuer_name, x509_serial_number, cert_digest, signing_time = certificate_data()
        
        signature = sign_data(line_xml)
        prop_cert_base64 = signed_properties_hash(signing_time, cert_digest, formatted_issuer_name, x509_serial_number)
        
        ubl_extension_string(doc_hash, prop_cert_base64, signature, certificate_base64, signing_time, cert_digest, formatted_issuer_name, x509_serial_number, line_xml)

        compliance_api_call(invoice_number)  #digital signature


        # signature_base64, certificate_hash_base64,certificate_pem,issuer_name, serial_number = sign_document_digest(encoded_hash)
        # namespaces,signing_time=signxml_modify(certificate_hash_base64, issuer_name, serial_number)
        # props_digest_value = signed_properties_hash()
        # print(f"PropsDigest: {props_digest_value}")

        #signed_properties_base64=generate_Signed_Properties_Hash(signing_time,issuer_name,serial_number,certificate_hash_base64)
        #populate_The_UBL_Extensions_Output(signature_base64, namespaces, signed_properties_base64, encoded_hash,certificate_pem)

        #signed_xmlfile_name = structuring_signedxml()


        #print("checking signed xm files",signed_xmlfile_name)   #localtion of file

        #print("Testing xml decode",xml_base64_Decode(signed_xmlfile_name))
        
        #hash = xml_sha256_hash(signed_xmlfile_name)
        #signed_xmlfile_name = xml_base64_Decode(signed_xmlfile_name)
        

        
       
       
       # compliance_api_call(hash, signed_xmlfile_name,invoice_number)  #digital signature
             
       
        #compliance_api_call(hash_hex, base64_encoded_xml,invoice_number)




        # # You might want to return or save the pretty_xml_string as needed
        # # return pretty_xml_string

    except Exception as e:
        print("ERROR: " + str(e))
        frappe.log_error(title='LHDN invoice call failed', message=get_traceback())

























