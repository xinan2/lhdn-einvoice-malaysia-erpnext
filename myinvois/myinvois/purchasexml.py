"""this file is used to generate the xml file for the invoice"""


import frappe
import os
import xml.etree.ElementTree as ET
from lxml import etree
import xml.dom.minidom as minidom
import uuid 
from frappe.utils import now
import re
from frappe.utils.data import  get_time
from datetime import datetime, timezone
import xml.etree.ElementTree as ET
import json
import xml.etree.ElementTree as ElementTree
from datetime import datetime, timedelta
from frappe import _
from myinvois.myinvois.createxml  import get_invoice_version,invoice_Typecode_Compliance,get_Tax_for_Item,aggregate_tax_by_type,tax_Data,get_tax_total_from_items,item_data




#Necessary imports for XML generation extension
def xml_tags():
    try: 
        invoice = ET.Element("Invoice", xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" )
        invoice.set("xmlns:cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
        invoice.set("xmlns:cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
        invoice.set("xmlns:ext", "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2")   

        return invoice
    except Exception as e:
            frappe.throw("error in xml tags formation:  "+ str(e) )


def create_element(parent, tag, text=None, attributes=None):
    """Creates an element with the given tag and text, and appends it to the parent element"""
    element = ET.SubElement(parent, tag, attributes or {})
    if text:
        element.text = text
    return element


def add_billing_reference(invoice,invoice_number,purchase_invoice_doc):
    """Adds BillingReference with InvoiceDocumentReference to the invoice"""
    try:
                
        billing_reference = ET.SubElement(invoice, "cac:BillingReference")        
        invoice_document_reference = ET.SubElement(billing_reference, "cac:InvoiceDocumentReference")   
        
        # if purchase_invoice_doc.custom_einvoice_type in [
        #     "Credit Note"
        # ]:
        #     invoice_id = purchase_invoice_doc.return_against

        # else:
        #     invoice_id = invoice_number

        invoice_id = invoice_number
        cbc_ID = ET.SubElement(invoice_document_reference, "cbc:ID")   
        cbc_ID.text = str(invoice_id) 

        
        # if purchase_invoice_doc.custom_einvoice_type in [
        #     "Credit Note",
           
        # ]:
        #     doc_id = purchase_invoice_doc.return_against
        #     if not doc_id:
        #         frappe.throw("No document found in return_against.")


        #     doc = frappe.get_doc("Sales Invoice", doc_id)

        #     if hasattr(doc, "custom_uuid") and doc.custom_uuid:
        #         print("enter in custom uuid block")                               
        #         uuid = doc.custom_uuid
        #         print("uuid",uuid)
        #         cbc_ID = ET.SubElement(invoice_document_reference, "cbc:UUID")   
        #         cbc_ID.text = str(uuid)                
        #     else:
        #         frappe.throw("No UUID documents no found in custom_uuid.")

    except (
        frappe.DoesNotExistError,
        frappe.ValidationError,
        AttributeError,
        KeyError,
    ) as e:
        frappe.msgprint(f"Error in add billing reference: {str(e)}")
        return None



def purchase_invoice_data(invoice,invoice_number):
    """Populate the purchase invoice data into the XML structure"""
    try:
        purchase_invoice_doc = frappe.get_doc('Purchase Invoice' ,invoice_number)

        create_element(invoice, "cbc:ID", str(purchase_invoice_doc.name))
        
        now_utc = datetime.now(timezone.utc)
        issue_date = now_utc.strftime("%Y-%m-%d")
        issue_time = now_utc.strftime("%H:%M:%SZ")

        create_element(invoice, "cbc:IssueDate", issue_date)
        create_element(invoice, "cbc:IssueTime", issue_time)
        
        if not purchase_invoice_doc.custom_einvoice_type:
            frappe.throw("Please select the e-invoice type in the sales invoice")

        compliance_type = purchase_invoice_doc.custom_einvoice_code 


        return compliance_type,invoice, purchase_invoice_doc


    except (
        frappe.DoesNotExistError,
        frappe.ValidationError,
        AttributeError,
        KeyError,
    ) as e:
        frappe.throw(_(f"Error Purchase Invoice data: {str(e)}"))
        return None
    
    


def company_Data(invoice,purchase_invoice_doc): #supplier company data
    """"Now company data method is basically supplier company data"""
    try:
        
        supplier_doc = frappe.get_doc("Supplier", purchase_invoice_doc.supplier)


        # address_list = frappe.get_list(
        #     "Address", 
        #     filters={"is_your_company_address": "1", "name": sales_invoice_doc.company_address}, 
        #     fields=["address_line1", "address_line2", "city", "pincode", "state","custom_state_codes"]
        # )
        
        if int(frappe.__version__.split(".")[0]) == 13:
            address = frappe.get_doc("Address", supplier_doc.primary_address)
        else:
            address = frappe.get_doc(
                "Address", supplier_doc.supplier_primary_address
            )

        # address_list = frappe.get_list("Address", filters={"is_your_company_address": "1"}, fields=["address_line1", "address_line2","city","pincode","state"])
        if not address:
            frappe.throw("LHDN requires proper address. Please add your Supplier address in Supplier master")
   

        #Supplier
        cac_AccountingSupplierParty = ET.SubElement(invoice, "cac:AccountingSupplierParty")
        cac_Party_1 = ET.SubElement(cac_AccountingSupplierParty, "cac:Party")

        # Supplier’s Malaysia Standard Industrial Classification (MSIC) Code
        cbc_IndustryClassificationCode = ET.SubElement(cac_Party_1, "cbc:IndustryClassificationCode")
        cbc_IndustryClassificationCode.text = supplier_doc.custom_msic_codes
        cbc_IndustryClassificationCode.set("name", supplier_doc.custom_misc_description)

        # Supplier’s TIN
        cac_PartyIdentification = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
        cbc_ID_2 = ET.SubElement(cac_PartyIdentification, "cbc:ID")
        cbc_ID_2.set("schemeID", "TIN")
        cbc_ID_2.text = str(supplier_doc.tax_id )
        
        #BRN    
        supplier_id_type = supplier_doc.custom_registration_type  # Example field to determine the type of ID
        supplier_id_number = supplier_doc.custom_registration_no  # Example field for the ID number
        cac_PartyIdentification_1 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
        cbc_ID_Identification = ET.SubElement(cac_PartyIdentification_1, "cbc:ID")
        if supplier_id_type == 'BRN':
            cbc_ID_Identification.set("schemeID", "BRN")
        elif supplier_id_type == 'NRIC':
            cbc_ID_Identification.set("schemeID", "NRIC")
        elif supplier_id_type == 'PASSPORT':
            cbc_ID_Identification.set("schemeID", "PASSPORT")
        elif supplier_id_type == 'ARMY':
            cbc_ID_Identification.set("schemeID", "ARMY")
        cbc_ID_Identification.text = str(supplier_id_number)  #temporary commenting
        # cbc_ID_Identification.text = "199701002338"

        # Supplier’s SST Registration Number
        if supplier_doc.custom_sst_registration_no:
            cac_PartyIdentification_3 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
            cbc_ID_SST = ET.SubElement(cac_PartyIdentification_3, "cbc:ID")
            cbc_ID_SST.set("schemeID", "SST")
            cbc_ID_SST.text = supplier_doc.custom_sst_registration_no
        else:
            cac_PartyIdentification_3 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
            cbc_ID_SST = ET.SubElement(cac_PartyIdentification_3, "cbc:ID")
            cbc_ID_SST.set("schemeID", "SST")
            cbc_ID_SST.text = "NA"

        # Supplier’s Tourism Tax Registration Number
        if supplier_doc.custom_tourism_tax_registration_number:
            cac_PartyIdentification_4 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
            cbc_ID_TTX = ET.SubElement(cac_PartyIdentification_4, "cbc:ID")
            cbc_ID_TTX.set("schemeID", "TTX")
            cbc_ID_TTX.text = supplier_doc.custom_tourism_tax_registration_number
        else:
            cac_PartyIdentification_4 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
            cbc_ID_TTX = ET.SubElement(cac_PartyIdentification_4, "cbc:ID")
            cbc_ID_TTX.set("schemeID", "TTX")
            cbc_ID_TTX.text = "NA"

        # Supplier’s Address
        # for address in address_list:
        cac_PostalAddress = ET.SubElement(cac_Party_1, "cac:PostalAddress")
        cbc_CityName = ET.SubElement(cac_PostalAddress, "cbc:CityName")
        cbc_CityName.text = address.city 
        print("City",cbc_CityName.text)

        #Postal Zone
        cbc_PostalZone = ET.SubElement(cac_PostalAddress, "cbc:PostalZone")
        cbc_PostalZone.text = address.pincode 
        print("postal zone",cbc_PostalZone.text)

        cbc_CountrySubentity = ET.SubElement(cac_PostalAddress, "cbc:CountrySubentityCode")
        cbc_CountrySubentity.text = address.custom_state_codes 
        # cbc_CountrySubentity.text = "14"
        print("CountrySubentityCode",cbc_CountrySubentity.text)          

        #Address Line
        cac_AddressLine_0 = ET.SubElement(cac_PostalAddress, "cac:AddressLine")
        cbc_Line_0 = ET.SubElement(cac_AddressLine_0, "cbc:Line")
        cbc_Line_0.text = address.address_line1 

        if address.address_line2:
            cac_AddressLine_1 = ET.SubElement(cac_PostalAddress, "cac:AddressLine")
            cbc_Line_1 = ET.SubElement(cac_AddressLine_1, "cbc:Line")
            cbc_Line_1.text = address.address_line2
            # break         
            
        cac_Country = ET.SubElement(cac_PostalAddress, "cac:Country")
        cbc_IdentificationCode = ET.SubElement(cac_Country, "cbc:IdentificationCode", {
            "listID": "ISO3166-1",
            "listAgencyID": "6"
        })
        cbc_IdentificationCode.text = address.custom_country_code if address.custom_country_code else "MYS"

        # Supplier’s Name
        cac_PartyLegalEntity = ET.SubElement(cac_Party_1, "cac:PartyLegalEntity")
        cbc_RegistrationName = ET.SubElement(cac_PartyLegalEntity, "cbc:RegistrationName")
        cbc_RegistrationName.text = supplier_doc.supplier_name

        # Supplier’s Contact Number        
        cac_Contact = ET.SubElement(cac_Party_1, "cac:Contact")
        cbc_Telephone = ET.SubElement(cac_Contact, "cbc:Telephone")
        cbc_Telephone.text = supplier_doc.custom_contact_no

        # Supplier’s e-mail
        if supplier_doc.custom_email:
            # cac_Contact = ET.SubElement(cac_Party_1, "cac:Contact")
            #new
            cbc_ElectronicMail = ET.SubElement(cac_Contact, "cbc:ElectronicMail")
            cbc_ElectronicMail.text = supplier_doc.custom_email
                   
        return invoice
    except Exception as e:
            frappe.throw("error occured in company data"+ str(e) )



#Company
#Buyer
def customer_Data(invoice,purchase_invoice_doc):
    """Company is customer"""
    """"Company data is basically Buyer data"""
    try:
        # customer_doc= frappe.get_doc("Customer",sales_invoice_doc.customer)
        company_doc = frappe.get_doc("Company",purchase_invoice_doc.company)
        
        
        #Buyer's Address
        address_list = frappe.get_list(
            "Address", 
            filters={"is_your_company_address": "1"}, 
            fields=["address_line1", "address_line2", "city", "pincode", "state","custom_state_codes"],
            order_by="creation asc",  # Ensures a consistent selection

        )
        
        if len(address_list) == 0:
            frappe.throw("LHDN requires proper address. Please add your company address in address master")

        address = address_list[0]


        cac_AccountingCustomerParty = ET.SubElement(invoice, "cac:AccountingCustomerParty")
        cac_Party_2 = ET.SubElement(cac_AccountingCustomerParty, "cac:Party")

        #Customer's TIN
        cac_PartyIdentification_1 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
        cbc_ID_4 = ET.SubElement(cac_PartyIdentification_1, "cbc:ID")
        cbc_ID_4.set("schemeID", "TIN")
        cbc_ID_4.text =company_doc.tax_id
        # cbc_ID_4.text ="C2584563200"  #dynamic

        #BRN
        customer_id_type = company_doc.custom_registration_type  
        customer_id_number = company_doc.company_registration  

        cac_PartyIdentification_2 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
        cbc_ID_Identification = ET.SubElement(cac_PartyIdentification_2, "cbc:ID")
        
        if customer_id_type == 'BRN':
            cbc_ID_Identification.set("schemeID", "BRN")
        elif customer_id_type == 'NRIC':
            cbc_ID_Identification.set("schemeID", "NRIC")
        elif customer_id_type == 'PASSPORT':
            cbc_ID_Identification.set("schemeID", "PASSPORT")
        elif customer_id_type == 'ARMY':
            cbc_ID_Identification.set("schemeID", "ARMY")             
        cbc_ID_Identification.text = customer_id_number

        if company_doc.custom_sst_registration_no:
            cac_PartyIdentification_3 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
            cbc_ID_SST = ET.SubElement(cac_PartyIdentification_3, "cbc:ID")
            cbc_ID_SST.set("schemeID", "SST")
            cbc_ID_SST.text = company_doc.custom_sst_registration_no
        else:
            cac_PartyIdentification_4 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
            cbc_ID_SST_1 = ET.SubElement(cac_PartyIdentification_4, "cbc:ID")
            cbc_ID_SST_1.set("schemeID", "SST")
            cbc_ID_SST_1.text = "NA"        
                            
        
                
        cac_PostalAddress = ET.SubElement(cac_Party_2, "cac:PostalAddress")

        cbc_CityName = ET.SubElement(cac_PostalAddress, "cbc:CityName")
        cbc_CityName.text = address.city 

        cbc_PostalZone = ET.SubElement(cac_PostalAddress, "cbc:PostalZone")
        cbc_PostalZone.text = address.pincode

        cbc_CountrySubentity = ET.SubElement(cac_PostalAddress, "cbc:CountrySubentityCode")
        # cbc_CountrySubentity.text = "14"
        cbc_CountrySubentity.text = address.custom_state_codes 

        cac_AddressLine_0 = ET.SubElement(cac_PostalAddress, "cac:AddressLine")
        cbc_Line_0 = ET.SubElement(cac_AddressLine_0, "cbc:Line")
        cbc_Line_0.text = address.address_line1 if address.address_line1 else "NA"

        if address.address_line2:
            cac_AddressLine_1 = ET.SubElement(cac_PostalAddress, "cac:AddressLine")
            cbc_Line_1 = ET.SubElement(cac_AddressLine_1, "cbc:Line")
            cbc_Line_1.text = address.address_line2
        
        cac_Country = ET.SubElement(cac_PostalAddress, "cac:Country")
        cbc_IdentificationCode = ET.SubElement(cac_Country, "cbc:IdentificationCode", {
            "listID": "ISO3166-1",
            "listAgencyID": "6"
        })
        cbc_IdentificationCode.text = address.custom_country_code if address.custom_country_code else "MYS"
            
        #Customer's Name
        cac_PartyLegalEntity_1 = ET.SubElement(cac_Party_2, "cac:PartyLegalEntity")
        cbc_RegistrationName_1 = ET.SubElement(cac_PartyLegalEntity_1, "cbc:RegistrationName")
        cbc_RegistrationName_1.text = purchase_invoice_doc.company

        # Customer’s Contact Number
        print("customer contact")
        cac_Contact = ET.SubElement(cac_Party_2, "cac:Contact")
        cbc_Telephone = ET.SubElement(cac_Contact, "cbc:Telephone")
        cbc_Telephone.text = company_doc.custom_contact_no
        
        if company_doc.email:
            # cac_Contact = ET.SubElement(cac_Party_2, "cac:Contact")
            cbc_ElectronicMail = ET.SubElement(cac_Contact, "cbc:ElectronicMail")
            cbc_ElectronicMail.text = company_doc.email
        
        return invoice
    except Exception as e:
            frappe.throw("error occured in customer data"+ str(e) )



def doc_Reference(invoice,purchase_invoice_doc,invoice_number):
    try:
        cbc_DocumentCurrencyCode = ET.SubElement(invoice, "cbc:DocumentCurrencyCode")
        cbc_DocumentCurrencyCode.text = purchase_invoice_doc.currency
        
        cbc_TaxCurrencyCode = ET.SubElement(invoice, "cbc:TaxCurrencyCode")
        cbc_TaxCurrencyCode.text = "MYR"  
        
        #invoice period
        inv_period = ET.SubElement(invoice, "cac:InvoicePeriod")        
        cbc_ID_start_date = ET.SubElement(inv_period, "cbc:StartDate")
        cbc_ID_start_date.text = str(purchase_invoice_doc.posting_date)
        
        cbc_ID_end_Date = ET.SubElement(inv_period, "cbc:EndDate")
        cbc_ID_end_Date.text = str(purchase_invoice_doc.due_date)
        
        cbc_Description = ET.SubElement(inv_period, "cbc:Description")
        cbc_Description.text = "Monthly"
        
        # Add BillingReference
        add_billing_reference(invoice,invoice_number,purchase_invoice_doc)
        
        return invoice  
    except Exception as e:
            frappe.throw("Error occured in  reference doc" + str(e) )




def xml_structuring(invoice,purchase_invoice_doc):
  
    raw_xml = ET.tostring(invoice, encoding='utf-8', method='xml').decode('utf-8')
    with open(frappe.local.site + "/private/files/create.xml", 'w') as file:
        file.write(raw_xml)
    try:
        fileXx = frappe.get_doc(
            {   "doctype": "File",        
                "file_type": "xml",  
                "file_name":  "E-invoice-" + purchase_invoice_doc.name + ".xml",
                "attached_to_doctype": purchase_invoice_doc.doctype,
                "attached_to_name": purchase_invoice_doc.name, 
                "content": raw_xml,
                "is_private": 1,})
        fileXx.save()


    except Exception as e:
                    frappe.throw(frappe.get_traceback())
    return raw_xml