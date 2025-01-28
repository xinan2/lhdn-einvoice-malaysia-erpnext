#utilites for myinvois

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






# This method is for digital signature
def xml_tags():
            try: 
                invoice = ET.Element("Invoice", xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2" )
                invoice.set("xmlns:cac", "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2")
                invoice.set("xmlns:cbc", "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2")
                invoice.set("xmlns:ext", "urn:oasis:names:specification:ubl:schema:xsd:CommonExtensionComponents-2")   

                return invoice
            except Exception as e:
                    frappe.throw("error in xml tags formation:  "+ str(e) )



#This method is fetching sales invoice data
def salesinvoice_data(invoice,invoice_number):
            try:
                print("enter in salesinvoicedata")
                sales_invoice_doc = frappe.get_doc('Sales Invoice' ,invoice_number)
                
                cbc_ID = ET.SubElement(invoice, "cbc:ID")   #initialize
                cbc_ID.text = str(sales_invoice_doc.name)  # assign


                # Get the current date and time in UTC
                now_utc = datetime.now(timezone.utc)
                issue_date = now_utc.date()
                issue_time = now_utc.time().replace(microsecond=0)  # Remove microseconds for cleaner output


                cbc_IssueDate = ET.SubElement(invoice, "cbc:IssueDate")
                cbc_IssueDate.text = str(issue_date)  #Erp sales invoice  posting_date
                # cbc_IssueDate.text = str(sales_invoice_doc.posting_date)  #Erp sales invoice  posting_date
                print("issue date ",cbc_IssueDate.text)
                # cbc_IssueDate.text = "2024-10-06"

                cbc_IssueTime = ET.SubElement(invoice, "cbc:IssueTime")
                cbc_IssueTime.text = issue_time.isoformat() + 'Z'
                # cbc_IssueTime.text = get_Issue_Time(invoice_number)       #Erp sales invoice  posting_time
                print("issue time",cbc_IssueTime.text)
                # cbc_IssueTime.text = "15:30:00Z"      #Erp sales invoice  posting_time

                # cbc_IssueTime.text = get_Issue_Time(invoice_number)       #Erp sales invoice  posting_time
                return invoice ,sales_invoice_doc
            except Exception as e:
                    frappe.throw("error occured in salesinvoice data"+ str(e) )




def company_Data(invoice,sales_invoice_doc): #supplier data
            try:
                company_doc = frappe.get_doc("Company", sales_invoice_doc.company)


                address_list = frappe.get_list(
                    "Address", 
                    filters={"is_your_company_address": "1", "name": sales_invoice_doc.company_address}, 
                    fields=["address_line1", "address_line2", "city", "pincode", "state","custom_state_codes"]
                )

                # address_list = frappe.get_list("Address", filters={"is_your_company_address": "1"}, fields=["address_line1", "address_line2","city","pincode","state"])


                if len(address_list) == 0:
                    frappe.throw("LHDN requires proper address. Please add your company address in address master")

            
                
                #Supplier
                cac_AccountingSupplierParty = ET.SubElement(invoice, "cac:AccountingSupplierParty")
                cac_Party_1 = ET.SubElement(cac_AccountingSupplierParty, "cac:Party")


                # Supplier’s Malaysia Standard Industrial Classification (MSIC) Code
                cbc_IndustryClassificationCode = ET.SubElement(cac_Party_1, "cbc:IndustryClassificationCode")
                cbc_IndustryClassificationCode.text = company_doc.custom_msic_codes
                cbc_IndustryClassificationCode.set("name", company_doc.custom_misc_description)


                # Supplier’s TIN
                cac_PartyIdentification = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
                cbc_ID_2 = ET.SubElement(cac_PartyIdentification, "cbc:ID")
                cbc_ID_2.set("schemeID", "TIN")
                cbc_ID_2.text = str(company_doc.tax_id )
                


                #BRN    
                supplier_id_type = company_doc.custom_registration_type  # Example field to determine the type of ID
                supplier_id_number = company_doc.company_registration  # Example field for the ID number
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
                if company_doc.custom_sst_registration_no:
                    cac_PartyIdentification_3 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
                    cbc_ID_SST = ET.SubElement(cac_PartyIdentification_3, "cbc:ID")
                    cbc_ID_SST.set("schemeID", "SST")
                    cbc_ID_SST.text = company_doc.custom_sst_registration_no
                else:
                    cac_PartyIdentification_3 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
                    cbc_ID_SST = ET.SubElement(cac_PartyIdentification_3, "cbc:ID")
                    cbc_ID_SST.set("schemeID", "SST")
                    cbc_ID_SST.text = "NA"

                # Supplier’s Tourism Tax Registration Number
                if company_doc.custom_tourism_tax_registration:
                    cac_PartyIdentification_4 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
                    cbc_ID_TTX = ET.SubElement(cac_PartyIdentification_4, "cbc:ID")
                    cbc_ID_TTX.set("schemeID", "TTX")
                    cbc_ID_TTX.text = company_doc.custom_tourism_tax_registration
                else:
                    cac_PartyIdentification_4 = ET.SubElement(cac_Party_1, "cac:PartyIdentification")
                    cbc_ID_TTX = ET.SubElement(cac_PartyIdentification_4, "cbc:ID")
                    cbc_ID_TTX.set("schemeID", "TTX")
                    cbc_ID_TTX.text = "NA"



                # Supplier’s Address
                for address in address_list:
                    cac_PostalAddress = ET.SubElement(cac_Party_1, "cac:PostalAddress")

                    print("address",address)

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

                    break
                    
                    
                cac_Country = ET.SubElement(cac_PostalAddress, "cac:Country")
                cbc_IdentificationCode = ET.SubElement(cac_Country, "cbc:IdentificationCode", {
                    "listID": "ISO3166-1",
                    "listAgencyID": "6"
                })
                cbc_IdentificationCode.text = address.custom_country_code if address.custom_country_code else "MYS"





                # Supplier’s Name
                cac_PartyLegalEntity = ET.SubElement(cac_Party_1, "cac:PartyLegalEntity")
                cbc_RegistrationName = ET.SubElement(cac_PartyLegalEntity, "cbc:RegistrationName")
                cbc_RegistrationName.text = sales_invoice_doc.company

                # Supplier’s Contact Number
                
                cac_Contact = ET.SubElement(cac_Party_1, "cac:Contact")
                cbc_Telephone = ET.SubElement(cac_Contact, "cbc:Telephone")
                cbc_Telephone.text = company_doc.custom_contact_no

                # Supplier’s e-mail
                if company_doc.email:
                    # cac_Contact = ET.SubElement(cac_Party_1, "cac:Contact")
                    cbc_ElectronicMail = ET.SubElement(cac_Contact, "cbc:ElectronicMail")
                    cbc_ElectronicMail.text = company_doc.email
                   

               

                return invoice
            except Exception as e:
                    frappe.throw("error occured in company data"+ str(e) )


#Customer
def customer_Data(invoice,sales_invoice_doc):
            try:
                customer_doc= frappe.get_doc("Customer",sales_invoice_doc.customer)


                cac_AccountingCustomerParty = ET.SubElement(invoice, "cac:AccountingCustomerParty")
                cac_Party_2 = ET.SubElement(cac_AccountingCustomerParty, "cac:Party")


                 #Customer's TIN
                #/ ubl:Invoice / cac:AccountingCustomerParty / cac:Party / cac:PartyIdentification / cbc:ID [@schemeID=’TIN’]
                cac_PartyIdentification_1 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
                cbc_ID_4 = ET.SubElement(cac_PartyIdentification_1, "cbc:ID")
                cbc_ID_4.set("schemeID", "TIN")
                cbc_ID_4.text =customer_doc.tax_id
                # cbc_ID_4.text ="C2584563200"  #dynamic


                #BRN
                customer_id_type = customer_doc.custom_registration_type  # Example field to determine the type of ID
                customer_id_number = customer_doc.custom_registration_no  # Example field for the ID number


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

                if customer_doc.custom_sst_registration_no:
                    cac_PartyIdentification_3 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
                    cbc_ID_SST = ET.SubElement(cac_PartyIdentification_3, "cbc:ID")
                    cbc_ID_SST.set("schemeID", "SST")
                    cbc_ID_SST.text = customer_doc.custom_sst_registration_no
                else:
                    cac_PartyIdentification_4 = ET.SubElement(cac_Party_2, "cac:PartyIdentification")
                    cbc_ID_SST_1 = ET.SubElement(cac_PartyIdentification_4, "cbc:ID")
                    cbc_ID_SST_1.set("schemeID", "SST")
                    cbc_ID_SST_1.text = "NA"
        
                                   
                #Buyer's Address
                if int(frappe.__version__.split('.')[0]) == 13:
                    address = frappe.get_doc("Address", sales_invoice_doc.customer_address)    #check
                else:
                    print("address else")
                    address = frappe.get_doc("Address", customer_doc.customer_primary_address) 
                
                #. / cac:Party / cac:PostalAddress / cac:AddressLine / cbc:Line
                cac_PostalAddress = ET.SubElement(cac_Party_2, "cac:PostalAddress")

                #. / cac:Party / cac:PostalAddress / cbc:CityName
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

                

                #. / cac:Party / cac:PostalAddress / cac:Country / cbc:IdentificationCode [@listID=’ISO3166-1’] [@listAgencyID=’6’]
                cac_Country = ET.SubElement(cac_PostalAddress, "cac:Country")
                # cbc_IdentificationCode = ET.SubElement(cac_Country, "cbc:IdentificationCode")
                cbc_IdentificationCode = ET.SubElement(cac_Country, "cbc:IdentificationCode", {
                    "listID": "ISO3166-1",
                    "listAgencyID": "6"
                })
                cbc_IdentificationCode.text = address.custom_country_code if address.custom_country_code else "MYS"
 

                 
                #Customer's Name
                #/ ubl:Invoice / cac:AccountingCustomerParty / cac:Party / cac:PartyLegalEntity / cbc:RegistrationName
                cac_PartyLegalEntity_1 = ET.SubElement(cac_Party_2, "cac:PartyLegalEntity")
                cbc_RegistrationName_1 = ET.SubElement(cac_PartyLegalEntity_1, "cbc:RegistrationName")
                cbc_RegistrationName_1.text = sales_invoice_doc.customer


                # Customer’s Contact Number
                # if customer_doc.customer_primary_contact:
                print("customer contact")
                cac_Contact = ET.SubElement(cac_Party_2, "cac:Contact")
                cbc_Telephone = ET.SubElement(cac_Contact, "cbc:Telephone")
                # cbc_Telephone.text = "+922222222234"  #dynamic
                # cbc_Telephone.text = customer_doc.mobile_no
                cbc_Telephone.text = address.phone


                
                if customer_doc.custom_email_address:
                    # cac_Contact = ET.SubElement(cac_Party_2, "cac:Contact")
                    cbc_ElectronicMail = ET.SubElement(cac_Contact, "cbc:ElectronicMail")
                    cbc_ElectronicMail.text = customer_doc.custom_email_address

                
                return invoice
            except Exception as e:
                    frappe.throw("error occured in customer data"+ str(e) )


def get_invoice_version():
    settings =  frappe.get_doc('Lhdn Settings')
    invoice_doc_version = settings.enable_digital_signature
    return invoice_doc_version

def invoice_Typecode_Compliance(invoice,compliance_type):

                
            try:
                                         
                invoice_doc_version = get_invoice_version()  #checking from lhdn setting doctype
                cbc_InvoiceTypeCode = ET.SubElement(invoice, "cbc:InvoiceTypeCode")
                
                if invoice_doc_version == 1:
                    print("Version cehcking",invoice_doc_version)
                    cbc_InvoiceTypeCode.set("listVersionID", "1.1")  # Current e-Invoice version
                
                if invoice_doc_version == 0:
                    print("Version cehcking",invoice_doc_version)
                    cbc_InvoiceTypeCode.set("listVersionID", "1.0")  # Current e-Invoice version



                if compliance_type == "1":  # Invoice
                    print("complinae type 1")
                    cbc_InvoiceTypeCode.text = "01"
                elif compliance_type == "2":  # Credit Note
                    cbc_InvoiceTypeCode.text = "02"
                elif compliance_type == "3":  # Debit Note
                    cbc_InvoiceTypeCode.text = "03"
                elif compliance_type == "4":  # Refund Note
                    cbc_InvoiceTypeCode.text = "04"
                elif compliance_type == "11":  # Self-billed Invoice
                    cbc_InvoiceTypeCode.text = "11"
                elif compliance_type == "12":  # Self-billed Credit Note
                    cbc_InvoiceTypeCode.text = "12"
                elif compliance_type == "13":  # Self-billed Debit Note
                    cbc_InvoiceTypeCode.text = "13"
                elif compliance_type == "14":  # Self-billed Refund Note
                    cbc_InvoiceTypeCode.text = "14"
                        
                return invoice
                
                
                
            except Exception as e:
                    frappe.throw("error occured in Compliance typecode"+ str(e) )



def doc_Reference(invoice,sales_invoice_doc,invoice_number):
            try:
                cbc_DocumentCurrencyCode = ET.SubElement(invoice, "cbc:DocumentCurrencyCode")
                cbc_DocumentCurrencyCode.text = sales_invoice_doc.currency
                
                cbc_TaxCurrencyCode = ET.SubElement(invoice, "cbc:TaxCurrencyCode")
                cbc_TaxCurrencyCode.text = "MYR"  # MYR is as LHDN requires tax amount in MYR
                
                # if sales_invoice_doc.is_return == 1:
                #                 invoice=billing_reference_for_credit_and_debit_note(invoice,sales_invoice_doc)
                # cac_AdditionalDocumentReference = ET.SubElement(invoice, "cac:AdditionalDocumentReference")
                # cbc_ID_1 = ET.SubElement(cac_AdditionalDocumentReference, "cbc:ID")
                # cbc_ID_1.text = "ICV"
                # cbc_UUID_1 = ET.SubElement(cac_AdditionalDocumentReference, "cbc:UUID")
                # cbc_UUID_1.text = str(get_ICV_code(invoice_number))
                return invoice  
            except Exception as e:
                    frappe.throw("Error occured in  reference doc" + str(e) )


def aggregate_tax_by_type(sales_invoice_doc):
    tax_by_type = {}
    for item in sales_invoice_doc.items:
        item_tax_amount, item_tax_percentage = get_Tax_for_Item(sales_invoice_doc.taxes[0].item_wise_tax_detail, item.item_code)
        tax_type = item.custom_lhdn_tax_type_code if item.custom_lhdn_tax_type_code else sales_invoice_doc.custom_lhdn_tax_type_code
        if tax_type not in tax_by_type:
            tax_by_type[tax_type] = {
                'tax_amount': 0.0,
                'tax_percentage': item_tax_percentage,
                'taxable_amount': 0.0
            }
        tax_by_type[tax_type]['tax_amount'] += item_tax_amount
        tax_by_type[tax_type]['taxable_amount'] += item.base_net_amount
    return tax_by_type


def tax_Data(invoice,sales_invoice_doc):
    try:
          
                ##########My code start##########
                
                #/ ubl:Invoice / cac:TaxTotal / cbc:TaxAmount [@currencyID=’MYR’]
                #Total Tax Amount

                #for foreign currency
                if sales_invoice_doc.currency != "MYR":
                    cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")
                    
                    cbc_TaxAmount_MYR = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                    cbc_TaxAmount_MYR.set("currencyID", "MYR") # MYR is as lhdn requires tax amount in lhdn
                    tax_amount_without_retention_myr =  round(sales_invoice_doc.conversion_rate * abs(get_tax_total_from_items(sales_invoice_doc)),2)
                    cbc_TaxAmount_MYR.text = str(round( tax_amount_without_retention_myr,2))     # str( abs(sales_invoice_doc.base_total_taxes_and_charges))
                #end for foreign currency
                
                
                #for MYR currency
                if sales_invoice_doc.currency == "MYR":
                    cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")
                    
                    cbc_TaxAmount_MYR = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                    cbc_TaxAmount_MYR.set("currencyID", "MYR") # MYR is as lhdn requires tax amount in MYR
                    tax_amount_without_retention_myr =  round(abs(get_tax_total_from_items(sales_invoice_doc)),2)
                    cbc_TaxAmount_MYR.text = str(round( tax_amount_without_retention_myr,2))     # str( abs(sales_invoice_doc.base_total_taxes_and_charges))
                #end for MYR currency
                
                #temporary
                # cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")
                # cbc_TaxAmount = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                # cbc_TaxAmount.set("currencyID", sales_invoice_doc.currency) # MYR is as LHDN requires tax amount in MYR
                # tax_amount_without_retention =  round(abs(get_tax_total_from_items(sales_invoice_doc)),2)
                # cbc_TaxAmount.text = str(round( tax_amount_without_retention,2))     # str( abs(sales_invoice_doc.base_total_taxes_and_charges))

                
                # Aggregate tax by type
                tax_by_type = aggregate_tax_by_type(sales_invoice_doc)

                # Aggregate tax by type
                tax_by_type = aggregate_tax_by_type(sales_invoice_doc)

                # Add each tax type to TaxTotal
                for tax_type, tax_data in tax_by_type.items():
                    
                    #/ ubl:Invoice / cac:TaxTotal / cac:TaxSubtotal / cbc:TaxAmount [@currencyID=’MYR’]
                    #Total Tax Amount Per Tax Type
                    cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, "cac:TaxSubtotal")

                    #Amount Exempted from Tax(Invoice level tax exemption)
                    cbc_TaxableAmount = ET.SubElement(cac_TaxSubtotal, "cbc:TaxableAmount")
                    cbc_TaxableAmount.set("currencyID", sales_invoice_doc.currency)
                    cbc_TaxableAmount.text =str(round(tax_data['taxable_amount'], 2))
                    # cbc_TaxableAmount.text =str(abs(round(sales_invoice_doc.base_net_total,2)))

                    # cbc_TaxableAmount.text =str(abs(round(sales_invoice_doc.base_net_total,2)))


                    cbc_TaxAmount_2 = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
                    cbc_TaxAmount_2.set("currencyID", sales_invoice_doc.currency)
                    cbc_TaxAmount_2.text = str(round(tax_data['tax_amount'], 2))
                    # cbc_TaxAmount_2.text = str(round( tax_amount_without_retention_myr,2)) 

                    cac_TaxCategory_1 = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")
                    cbc_ID_8 = ET.SubElement(cac_TaxCategory_1, "cbc:ID")
        
                    if sales_invoice_doc.custom_lhdn_tax_type_code  == 'E':   #Tax Exemption                
                        
                        
                        
                        #Details of Tax Exemption (Invoice level tax exemption)
                        # cac_TaxCategory_1 = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")
                        # cbc_ID_8 = ET.SubElement(cac_TaxCategory_1, "cbc:ID")
                        cbc_ID_8.text = "E"

                        # cbc_ID_8.text = str(sales_invoice_doc.custom_lhdn_tax_type_code)


                        cbc_TaxExemptionReason = ET.SubElement(cac_TaxCategory_1, "cbc:TaxExemptionReason")
                        cbc_TaxExemptionReason.text = sales_invoice_doc.custom_exemption_description


                        # cac_TaxScheme = ET.SubElement(cac_TaxCategory_1, "cac:TaxScheme")
                        # cbc_TaxSchemeID = ET.SubElement(cac_TaxScheme, "cbc:ID")
                        # cbc_TaxSchemeID.set("schemeID", "UN/ECE 5153")
                        # cbc_TaxSchemeID.set("schemeAgencyID", "6")
                        # cbc_TaxSchemeID.text = "OTH"

                    else:
                        #Details of Tax Exemption (Invoice level tax exemption)
                        # cac_TaxCategory_1 = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")
                        # cbc_ID_8 = ET.SubElement(cac_TaxCategory_1, "cbc:ID")
                        cbc_ID_8.text = str(tax_type)
                        # cbc_ID_8.text = str(sales_invoice_doc.custom_lhdn_tax_type_code)

                        # # Tax Rate in percentage
                        # cbc_TaxRatePercent = ET.SubElement(cac_TaxCategory_1, "cbc:Percent")
                        # cbc_TaxRatePercent.text =  f"{float(sales_invoice_doc.taxes[0].rate):.2f}" 

                    cac_TaxScheme = ET.SubElement(cac_TaxCategory_1, "cac:TaxScheme")
                    cbc_TaxSchemeID = ET.SubElement(cac_TaxScheme, "cbc:ID")
                    cbc_TaxSchemeID.set("schemeID", "UN/ECE 5153")
                    cbc_TaxSchemeID.set("schemeAgencyID", "6")
                    cbc_TaxSchemeID.text = "OTH"

                      





                
                # / ubl:Invoice / cac:LegalMonetaryTotal / cbc:TaxExclusiveAmount [@currencyID=’MYR’]

                #Total Excluding Tax
                cac_LegalMonetaryTotal = ET.SubElement(invoice, "cac:LegalMonetaryTotal")
                cbc_TaxExclusiveAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:TaxExclusiveAmount")
                cbc_TaxExclusiveAmount.set("currencyID", sales_invoice_doc.currency)
                cbc_TaxExclusiveAmount.text = str(abs(sales_invoice_doc.net_total))

        
                #/ ubl:Invoice / cac:LegalMonetaryTotal / cbc:TaxInclusiveAmount [@currencyID=’MYR’]
                #Total Including Tax
                cbc_TaxInclusiveAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:TaxInclusiveAmount")
                cbc_TaxInclusiveAmount.set("currencyID", sales_invoice_doc.currency)
                tax_amount_without_retention =  round(abs(get_tax_total_from_items(sales_invoice_doc)),2)
                cbc_TaxInclusiveAmount.text = str(round(abs(sales_invoice_doc.net_total) + abs(tax_amount_without_retention),2))


                #Total Payable Amount
                cbc_PayableAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:PayableAmount")
                cbc_PayableAmount.set("currencyID", sales_invoice_doc.currency)
                cbc_PayableAmount.text = str(round(abs(sales_invoice_doc.net_total) + abs(tax_amount_without_retention),2))

                

                                                                                 
                ###########My code End#########        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
                # cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")              
                # cbc_TaxAmount = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                # cbc_TaxAmount.set("currencyID", sales_invoice_doc.currency) # SAR is as zatca requires tax amount in SAR
                # tax_amount_without_retention =  round(abs(get_tax_total_from_items(sales_invoice_doc)),2)
                # cbc_TaxAmount.text = str(round( tax_amount_without_retention,2))     # str( abs(sales_invoice_doc.base_total_taxes_and_charges))
                # cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, "cac:TaxSubtotal")
                # cbc_TaxableAmount = ET.SubElement(cac_TaxSubtotal, "cbc:TaxableAmount")
                # cbc_TaxableAmount.set("currencyID", sales_invoice_doc.currency)
                # cbc_TaxableAmount.text =str(abs(round(sales_invoice_doc.base_net_total,2)))
                # cbc_TaxAmount_2 = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
                # cbc_TaxAmount_2.set("currencyID", sales_invoice_doc.currency)
                
                # cbc_TaxAmount_2.text = str(tax_amount_without_retention) # str(abs(sales_invoice_doc.base_total_taxes_and_charges))
                # cac_TaxCategory_1 = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")
                # cbc_ID_8 = ET.SubElement(cac_TaxCategory_1, "cbc:ID")
                # if sales_invoice_doc.custom_zatca_tax_category == "Standard":
                #     cbc_ID_8.text = "S"
                # elif sales_invoice_doc.custom_zatca_tax_category == "Zero Rated":
                #     cbc_ID_8.text = "Z"
                # elif sales_invoice_doc.custom_zatca_tax_category == "Exempted":
                #     cbc_ID_8.text = "E"
                # elif sales_invoice_doc.custom_zatca_tax_category == "Services outside scope of tax / Not subject to VAT":
                #     cbc_ID_8.text = "O"
                # cbc_Percent_1 = ET.SubElement(cac_TaxCategory_1, "cbc:Percent")
                # # cbc_Percent_1.text = str(sales_invoice_doc.taxes[0].rate)
                # cbc_Percent_1.text = f"{float(sales_invoice_doc.taxes[0].rate):.2f}" 
                # exemption_reason_map = get_exemption_reason_map()
                # if sales_invoice_doc.custom_zatca_tax_category != "Standard":
                #     cbc_TaxExemptionReasonCode = ET.SubElement(cac_TaxCategory_1, "cbc:TaxExemptionReasonCode")
                #     cbc_TaxExemptionReasonCode.text = sales_invoice_doc.custom_exemption_reason_code
                #     cbc_TaxExemptionReason = ET.SubElement(cac_TaxCategory_1, "cbc:TaxExemptionReason")
                #     reason_code = sales_invoice_doc.custom_exemption_reason_code
                #     if reason_code in exemption_reason_map:
                #         cbc_TaxExemptionReason.text = exemption_reason_map[reason_code]       
                # cac_TaxScheme_3 = ET.SubElement(cac_TaxCategory_1, "cac:TaxScheme")
                # cbc_ID_9 = ET.SubElement(cac_TaxScheme_3, "cbc:ID")
                # cbc_ID_9.text = "VAT"
                
                # # cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")
                # # cbc_TaxAmount = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                # # cbc_TaxAmount.set("currencyID", sales_invoice_doc.currency)
                # # cbc_TaxAmount.text =str(round(tax_amount_without_retention,2))
                
                # cac_LegalMonetaryTotal = ET.SubElement(invoice, "cac:LegalMonetaryTotal")
                # cbc_LineExtensionAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:LineExtensionAmount")
                # cbc_LineExtensionAmount.set("currencyID", sales_invoice_doc.currency)
                # cbc_LineExtensionAmount.text =  str(abs(sales_invoice_doc.base_net_total))
                # cbc_TaxExclusiveAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:TaxExclusiveAmount")
                # cbc_TaxExclusiveAmount.set("currencyID", sales_invoice_doc.currency)
                # cbc_TaxExclusiveAmount.text = str(abs(sales_invoice_doc.net_total))
                # cbc_TaxInclusiveAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:TaxInclusiveAmount")
                # cbc_TaxInclusiveAmount.set("currencyID", sales_invoice_doc.currency)
                # cbc_TaxInclusiveAmount.text = str(round(abs(sales_invoice_doc.net_total) + abs(tax_amount_without_retention),2))
                # cbc_AllowanceTotalAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:AllowanceTotalAmount")
                # cbc_AllowanceTotalAmount.set("currencyID", sales_invoice_doc.currency)
                # cbc_AllowanceTotalAmount.text = str(sales_invoice_doc.base_change_amount)
                # cbc_PayableAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:PayableAmount")
                # cbc_PayableAmount.set("currencyID", sales_invoice_doc.currency)
                # cbc_PayableAmount.text = str(round(abs(sales_invoice_doc.net_total) + abs(tax_amount_without_retention),2))
                return invoice
             
    except Exception as e:
                    frappe.throw("error occured in tax data"+ str(e) )  



def item_data(invoice, sales_invoice_doc):
    try:
        for single_item in sales_invoice_doc.items:
            item_tax_amount, item_tax_percentage = get_Tax_for_Item(sales_invoice_doc.taxes[0].item_wise_tax_detail, single_item.item_code)
            
            
            # Create InvoiceLine element
            cac_InvoiceLine = ET.SubElement(invoice, "cac:InvoiceLine")
            
            #ID
            cbc_ID_10 = ET.SubElement(cac_InvoiceLine, "cbc:ID")
            cbc_ID_10.text = str(single_item.idx)


            # Quantity 
            cbc_InvoicedQuantity = ET.SubElement(cac_InvoiceLine, "cbc:InvoicedQuantity")
            # cbc_InvoicedQuantity.set("unitCode", str(single_item.uom))
            cbc_InvoicedQuantity.text = str(abs(single_item.qty))         



            # Total Excluding Tax
            cbc_LineExtensionAmount_1 = ET.SubElement(cac_InvoiceLine, "cbc:LineExtensionAmount")   #100
            cbc_LineExtensionAmount_1.set("currencyID", sales_invoice_doc.currency)
            cbc_LineExtensionAmount_1.text = str(single_item.base_net_amount)    #including only charges or discount and exclsing tax



            
            
            # Tax Type  / ubl:Invoice / cac:InvoiceLine / cac:TaxTotal / cac:TaxSubtotal / cac:TaxCategory / cbc:ID 
            cac_TaxTotal = ET.SubElement(cac_InvoiceLine, "cac:TaxTotal")
           



            if single_item.custom_lhdn_tax_type_code == "E":  # lhdn Tax type  Exempted


                # # Tax Amount   / ubl:Invoice / cac:InvoiceLine / cac:TaxTotal / cbc:TaxAmount [@currencyID=’MYR’]
                cbc_TaxAmount_3 = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                cbc_TaxAmount_3.set("currencyID", sales_invoice_doc.currency)
                cbc_TaxAmount_3.text = "0"
                # cbc_TaxAmount_3.text = str(abs(round(item_tax_percentage * single_item.base_net_amount / 100, 2)))  # 100 * 6 % = 6


                #TaxSubtotal
                cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, "cac:TaxSubtotal")
       

                #Amount Exempted from Tax(Invoice level tax exemption)
                cbc_TaxableAmount = ET.SubElement(cac_TaxSubtotal, "cbc:TaxableAmount")
                cbc_TaxableAmount.set("currencyID", sales_invoice_doc.currency)
                cbc_TaxableAmount.text = str(single_item.base_net_amount)   # 100  # #including only charges or discount and exclsing tax
                # cbc_TaxableAmount.text = str(abs(round(sales_invoice_doc.base_net_total,2)))               
              
                #tax amount                
                cbc_TaxAmount_2 = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
                cbc_TaxAmount_2.set("currencyID", sales_invoice_doc.currency)                
                cbc_TaxAmount_2.text = "0"

                cac_TaxCategory = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")            
                cbc_TaxCategoryID = ET.SubElement(cac_TaxCategory, "cbc:ID")
                cbc_TaxCategoryID.text = "E" # set taxable type provided by lhdn
                # cbc_TaxCategoryID.text = single_item.custom_lhdn_tax_code  # set taxable type provided by lhdn

                # Details of Tax Exemption
                cbc_TaxExemptionReason = ET.SubElement(cac_TaxCategory, "cbc:TaxExemptionReason")
                cbc_TaxExemptionReason.text = single_item.description

                cac_TaxScheme = ET.SubElement(cac_TaxCategory, "cac:TaxScheme")
                cbc_TaxSchemeID = ET.SubElement(cac_TaxScheme, "cbc:ID")
                cbc_TaxSchemeID.set("schemeID", "UN/ECE 5153")
                cbc_TaxSchemeID.set("schemeAgencyID", "6")
                cbc_TaxSchemeID.text = "OTH"


            else:
            
                # # Tax Amount   / ubl:Invoice / cac:InvoiceLine / cac:TaxTotal / cbc:TaxAmount [@currencyID=’MYR’]
                cbc_TaxAmount_3 = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
                cbc_TaxAmount_3.set("currencyID", sales_invoice_doc.currency)   #Tax Amount of each item
                cbc_TaxAmount_3.text = str(abs(round(item_tax_percentage * single_item.base_net_amount / 100, 2)))  # 100 * 6 % = 6


                #if Tax Rate in percentage then we add tabsubtotal so in this way we ahve to add lineextensionamount as it is in taxablemaount

                #TaxSubtotal
                cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, "cac:TaxSubtotal")


                #Amount Exempted from Tax(Invoice level tax exemption)
                cbc_TaxableAmount = ET.SubElement(cac_TaxSubtotal, "cbc:TaxableAmount")
                cbc_TaxableAmount.set("currencyID", sales_invoice_doc.currency)
                cbc_TaxableAmount.text = str(single_item.base_net_amount)   # 100  # #including only charges or discount and exclsing tax

            
                cbc_TaxAmount_2 = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
                cbc_TaxAmount_2.set("currencyID", sales_invoice_doc.currency)                
                cbc_TaxAmount_2.text =  str(abs(round(item_tax_percentage * single_item.base_net_amount / 100, 2)))  # 100 * 6 % = 6

                  
                cac_TaxCategory = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")            
                
                cbc_TaxCategoryID = ET.SubElement(cac_TaxCategory, "cbc:ID")
                cbc_TaxCategoryID.text = single_item.custom_lhdn_tax_type_code if single_item.custom_lhdn_tax_type_code else sales_invoice_doc.custom_lhdn_tax_type_code  # set taxable type provided by lhdn

                # Tax Rate in percentage
                cbc_TaxRatePercent = ET.SubElement(cac_TaxCategory, "cbc:Percent")
                cbc_TaxRatePercent.text = f"{item_tax_percentage:.2f}"

                

                cac_TaxScheme = ET.SubElement(cac_TaxCategory, "cac:TaxScheme")
                cbc_TaxSchemeID = ET.SubElement(cac_TaxScheme, "cbc:ID")
                cbc_TaxSchemeID.set("schemeID", "UN/ECE 5153")
                cbc_TaxSchemeID.set("schemeAgencyID", "6")
                cbc_TaxSchemeID.text = "OTH"



           
            # Item
            cac_Item = ET.SubElement(cac_InvoiceLine, "cac:Item")
           
            # Description of Product or Service
            cbc_Description = ET.SubElement(cac_Item, "cbc:Description")
            cbc_Description.text = single_item.description

            #Classification
            cac_CommodityClassification = ET.SubElement(cac_Item, "cac:CommodityClassification")
            cbc_ItemClassificationCode = ET.SubElement(cac_CommodityClassification, "cbc:ItemClassificationCode")
            cbc_ItemClassificationCode.set("listID", "CLASS")
            cbc_ItemClassificationCode.text = single_item.custom_item_classification_code

            # Unit Price
            cac_Price = ET.SubElement(cac_InvoiceLine, "cac:Price")            
            cbc_PriceAmount = ET.SubElement(cac_Price, "cbc:PriceAmount")
            cbc_PriceAmount.set("currencyID", sales_invoice_doc.currency)
            cbc_PriceAmount.text = str(abs(single_item.base_net_rate))


            # Subtotal
            cac_ItemPriceExtension = ET.SubElement(cac_InvoiceLine, "cac:ItemPriceExtension")
            cbc_Amount = ET.SubElement(cac_ItemPriceExtension, "cbc:Amount")
            cbc_Amount.set("currencyID", sales_invoice_doc.currency)
            cbc_Amount.text = str((single_item.base_price_list_rate) * (single_item.qty))   #excluding any charges , discount and tax
                                    
        



    
            # cbc_TaxSubtotalAmount = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
            # cbc_TaxSubtotalAmount.set("currencyID", "MYR")
            # cbc_TaxSubtotalAmount.text = cbc_TaxAmount_3.text

            # if sales_invoice_doc.taxes_and_charges == "Exempted":
            #     cbc_TaxCategoryID.text = "E"

            #     # Details of Tax Exemption
            #     cbc_TaxExemptionReason = ET.SubElement(cac_TaxCategory, "cbc:TaxExemptionReason")
            #     cbc_TaxExemptionReason.text = "Goods acquired with SST exemption under Sales Tax Act 2018. Reference No: (C01-2345-67890123)"

            #     cbc_TaxableAmount = ET.SubElement(cac_TaxSubtotal, "cbc:TaxableAmount")
            #     cbc_TaxableAmount.set("currencyID", "MYR")
            #     cbc_TaxableAmount.text = str(abs(single_item.base_net_amount))

            #     cbc_TaxAmount_3.text = "0.00"
            #     cbc_TaxSubtotalAmount.text = "0.00"

            # # Subtotal
            # cac_ItemPriceExtension = ET.SubElement(cac_InvoiceLine, "cac:ItemPriceExtension")
            # cbc_Amount = ET.SubElement(cac_ItemPriceExtension, "cbc:Amount")
            # cbc_Amount.set("currencyID", sales_invoice_doc.currency)
            # cbc_Amount.text = str(single_item.base_net_amount)

            # # Total Excluding Tax
            # cbc_LineExtensionAmount_1 = ET.SubElement(cac_InvoiceLine, "cbc:LineExtensionAmount")
            # cbc_LineExtensionAmount_1.set("currencyID", sales_invoice_doc.currency)
            # cbc_LineExtensionAmount_1.text = str(single_item.base_net_amount)

        return invoice
    except Exception as e:
        frappe.throw("Error occurred in item data: " + str(e))

def  get_Issue_Time(invoice_number): 
                doc = frappe.get_doc("Sales Invoice", invoice_number)
                time = get_time(doc.posting_time)
                # issue_time = time.strftime("%H:%M:%S")  #time in format of  hour,mints,secnds
                issue_time = time.strftime('%H:%M:%SZ')  #time in format of  hour,mints,secnds

                # utc_now = datetime.utcnow().replace(tzinfo=timezone.utc)
                # issue_time = utc_now.strftime('%H:%M:%SZ') 
                return issue_time

def get_Tax_for_Item(full_string, item):
    try:
        data = json.loads(full_string)
        tax_percentage = data.get(item, [0, 0])[0]
        tax_amount = data.get(item, [0, 0])[1]
        return tax_amount, tax_percentage
    except Exception as e:
        frappe.throw("Error occurred in tax for item: " + str(e))



def get_tax_total_from_items(sales_invoice_doc):
            try:
                total_tax = 0
                for single_item in sales_invoice_doc.items : 
                    item_tax_amount,tax_percent =  get_Tax_for_Item(sales_invoice_doc.taxes[0].item_wise_tax_detail,single_item.item_code)
                    total_tax = total_tax + (single_item.net_amount * (tax_percent/100))
                return total_tax 
            except Exception as e:
                    frappe.throw("Error occured in get_tax_total_from_items "+ str(e) )










































def set_total_amounts(invoice, sales_invoice_doc):
    try:
        # Legal Monetary Total
        cac_LegalMonetaryTotal = ET.SubElement(invoice, "cac:LegalMonetaryTotal")
        
        # Total Excluding Tax
        cbc_TaxExclusiveAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:TaxExclusiveAmount")
        cbc_TaxExclusiveAmount.set("currencyID", sales_invoice_doc.currency)
        # cbc_TaxExclusiveAmount.text = str(abs(sales_invoice_doc.total_net_amount))
        cbc_TaxExclusiveAmount.text = str(abs(sales_invoice_doc.net_total))
        



        # Total Including Tax
        cbc_TaxInclusiveAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:TaxInclusiveAmount")
        cbc_TaxInclusiveAmount.set("currencyID", sales_invoice_doc.currency)
        cbc_TaxInclusiveAmount.text = str(abs(sales_invoice_doc.net_total))

    
        
        # Total Payable Amount
        cbc_PayableAmount = ET.SubElement(cac_LegalMonetaryTotal, "cbc:PayableAmount")
        cbc_PayableAmount.set("currencyID", sales_invoice_doc.currency)
        cbc_PayableAmount.text = str(abs(sales_invoice_doc.rounded_total))
        
        return invoice
    except Exception as e:
        frappe.throw("Error occurred in setting total amounts: " + str(e))


#Total Tax Amount / Total Tax Amount Per Tax Type
def set_tax_amounts(invoice, sales_invoice_doc):
    try:
        # Total Tax Amount
        cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")
        
        # Total Tax Amount
        cbc_TaxAmount = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
        cbc_TaxAmount.set("currencyID", sales_invoice_doc.currency)
        cbc_TaxAmount.text = str(abs(sales_invoice_doc.total_tax_amount))
        
        # Total Tax Amount Per Tax Type
        for tax_detail in sales_invoice_doc.taxes:
            cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, "cac:TaxSubtotal")
            
            # Tax Amount per Tax Type
            cbc_TaxAmount_Per_Tax_Type = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
            cbc_TaxAmount_Per_Tax_Type.set("currencyID", sales_invoice_doc.currency)
            cbc_TaxAmount_Per_Tax_Type.text = str(abs(tax_detail.tax_amount))
            
            # Additional details can be added here if needed, such as TaxCategory and TaxScheme
            cac_TaxCategory = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")
            cbc_ID = ET.SubElement(cac_TaxCategory, "cbc:ID")
            cbc_ID.text = tax_detail.tax_type
            
            cac_TaxScheme = ET.SubElement(cac_TaxCategory, "cac:TaxScheme")
            cbc_TaxScheme_ID = ET.SubElement(cac_TaxScheme, "cbc:ID")
            cbc_TaxScheme_ID.set("schemeID", "UN/ECE 5153")
            cbc_TaxScheme_ID.set("schemeAgencyID", "6")
            cbc_TaxScheme_ID.text = "OTH"

        return invoice
    except Exception as e:
        frappe.throw("Error occurred in setting tax amounts: " + str(e))


#tax type for main form
def set_tax_type_main_form(invoice, sales_invoice_doc):
    try:
        # Tax Total
        cac_TaxTotal = ET.SubElement(invoice, "cac:TaxTotal")

        # Total Tax Amount
        cbc_TaxAmount = ET.SubElement(cac_TaxTotal, "cbc:TaxAmount")
        cbc_TaxAmount.set("currencyID", sales_invoice_doc.currency)
        cbc_TaxAmount.text = str(abs(sales_invoice_doc.total_taxes_and_charges))
        
        # Iterate over each tax detail to set the Tax Type
        for tax_detail in sales_invoice_doc.taxes:
            cac_TaxSubtotal = ET.SubElement(cac_TaxTotal, "cac:TaxSubtotal")
            
            # Tax Amount per Tax Type
            cbc_TaxAmount_Per_Tax_Type = ET.SubElement(cac_TaxSubtotal, "cbc:TaxAmount")
            cbc_TaxAmount_Per_Tax_Type.set("currencyID", sales_invoice_doc.currency)
            cbc_TaxAmount_Per_Tax_Type.text = str(abs(tax_detail.tax_amount))
            
            # Tax Category
            cac_TaxCategory = ET.SubElement(cac_TaxSubtotal, "cac:TaxCategory")
            cbc_ID = ET.SubElement(cac_TaxCategory, "cbc:ID")
            # cbc_ID.text = tax_detail.tax_type  # e.g., '01' for sales tax
            cbc_ID.text = '01'  # e.g., '01' for sales tax


            # Tax Scheme
            cac_TaxScheme = ET.SubElement(cac_TaxCategory, "cac:TaxScheme")
            cbc_TaxScheme_ID = ET.SubElement(cac_TaxScheme, "cbc:ID")
            cbc_TaxScheme_ID.set("schemeID", "UN/ECE 5153")
            cbc_TaxScheme_ID.set("schemeAgencyID", "6")
            cbc_TaxScheme_ID.text = "OTH"  # This should be set to 'OTH' as per the requirement

        return invoice
    except Exception as e:
        frappe.throw("Error occurred in setting tax type: " + str(e))


def xml_structuring(invoice,sales_invoice_doc):
  
    raw_xml = ET.tostring(invoice, encoding='utf-8', method='xml').decode('utf-8')
    with open(frappe.local.site + "/private/files/create.xml", 'w') as file:
        file.write(raw_xml)
    try:
                    fileXx = frappe.get_doc(
                        {   "doctype": "File",        
                            "file_type": "xml",  
                            "file_name":  "E-invoice-" + sales_invoice_doc.name + ".xml",
                            "attached_to_doctype":sales_invoice_doc.doctype,
                            "attached_to_name":sales_invoice_doc.name, 
                            "content": raw_xml,
                            "is_private": 1,})
                    fileXx.save()


    except Exception as e:
                    frappe.throw(frappe.get_traceback())
    return raw_xml


# def xml_structuring(invoice,sales_invoice_doc):
#             try:
#                 xml_declaration = "<?xml version='1.0' encoding='UTF-8'?>\n"
#                 tree = ET.ElementTree(invoice)
#                 with open(frappe.local.site + "/private/files/xml_files.xml", 'wb') as file:
#                     tree.write(file, encoding='utf-8', xml_declaration=True)
#                 with open(frappe.local.site + "/private/files/xml_files.xml", 'r') as file:
#                     xml_string = file.read()
#                 xml_dom = minidom.parseString(xml_string)
#                 pretty_xml_string = xml_dom.toprettyxml(indent="  ")   # created xml into formatted xml form 
#                 print("Main pretty xml string",pretty_xml_string)
#                 with open(frappe.local.site + "/private/files/finalzatcaxml.xml", 'w') as file:
#                     file.write(pretty_xml_string)
#                           # Attach the getting xml for each invoice
#                 try:
#                     if frappe.db.exists("File",{ "attached_to_name": sales_invoice_doc.name, "attached_to_doctype": sales_invoice_doc.doctype }):
#                         frappe.db.delete("File",{ "attached_to_name":sales_invoice_doc.name, "attached_to_doctype": sales_invoice_doc.doctype })
#                 except Exception as e:
#                     frappe.throw(frappe.get_traceback())
                
#                 try:
#                     fileX = frappe.get_doc(
#                         {   "doctype": "File",        
#                             "file_type": "xml",  
#                             "file_name":  "E-invoice-" + sales_invoice_doc.name + ".xml",
#                             "attached_to_doctype":sales_invoice_doc.doctype,
#                             "attached_to_name":sales_invoice_doc.name, 
#                             "content": pretty_xml_string,
#                             "is_private": 1,})
#                     fileX.save()
#                 except Exception as e:
#                     frappe.throw(frappe.get_traceback())
                
#                 try:
#                     frappe.db.get_value('File', {'attached_to_name':sales_invoice_doc.name, 'attached_to_doctype': sales_invoice_doc.doctype}, ['file_name'])
#                 except Exception as e:
#                     frappe.throw(frappe.get_traceback())
#             except Exception as e:
#                     frappe.throw("Error occured in XML structuring and attach. Please contact your system administrator"+ str(e) )



## zatacasdk
# def xml_structuring(invoice,sales_invoice_doc):
#             try:
#                 print("enter in xml structuring")
#                 xml_declaration = "<?xml version='1.0' encoding='UTF-8'?>\n"
#                 tree = ET.ElementTree(invoice)
#                 with open(f"xml_files.xml", 'wb') as file:
#                     tree.write(file, encoding='utf-8', xml_declaration=True)
#                 with open(f"xml_files.xml", 'r') as file:
#                     xml_string = file.read()
#                 xml_dom = minidom.parseString(xml_string)
#                 pretty_xml_string = xml_dom.toprettyxml(indent="  ")   # created xml into formatted xml form 
#                 print("pretty_xml_string",pretty_xml_string)
#                 with open(f"finalzatcaxml.xml", 'w') as file:        #need to change
#                     file.write(pretty_xml_string)
#                           # Attach the getting xml for each invoice
#                 try:
#                     if frappe.db.exists("File",{ "attached_to_name": sales_invoice_doc.name, "attached_to_doctype": sales_invoice_doc.doctype }):
#                         frappe.db.delete("File",{ "attached_to_name":sales_invoice_doc.name, "attached_to_doctype": sales_invoice_doc.doctype })
#                 except Exception as e:
#                     frappe.throw(frappe.get_traceback())
                
#                 try:
#                     fileX = frappe.get_doc(
#                         {   "doctype": "File",        
#                             "file_type": "xml",  
#                             "file_name":  "E-invoice-" + sales_invoice_doc.name + ".xml",
#                             "attached_to_doctype":sales_invoice_doc.doctype,
#                             "attached_to_name":sales_invoice_doc.name, 
#                             "content": pretty_xml_string,
#                             "is_private": 1,})
#                     fileX.save()
#                 except Exception as e:
#                     frappe.throw(frappe.get_traceback())
                
#                 try:
#                     frappe.db.get_value('File', {'attached_to_name':sales_invoice_doc.name, 'attached_to_doctype': sales_invoice_doc.doctype}, ['file_name'])
#                 except Exception as e:
#                     frappe.throw(frappe.get_traceback())
#             except Exception as e:
#                     frappe.throw("Error occured in XML structuring and attach. Please contact your system administrator"+ str(e) )










































def get_ICV_code(invoice_number):
                try:
                    icv_code =  re.sub(r'\D', '', invoice_number)   # taking the number part only from doc name
                    return icv_code
                except Exception as e:
                    frappe.throw("error in getting icv number:  "+ str(e) )
                    

  




def invoice_Typecode_Simplified(invoice,sales_invoice_doc):
            try:                             
                cbc_InvoiceTypeCode = ET.SubElement(invoice, "cbc:InvoiceTypeCode")
                if sales_invoice_doc.is_return == 0:         
                    cbc_InvoiceTypeCode.set("name", "0200000") # Simplified
                    cbc_InvoiceTypeCode.text = "388"
                elif sales_invoice_doc.is_return == 1:       # return items and simplified invoice
                    cbc_InvoiceTypeCode.set("name", "0200000")  # Simplified
                    cbc_InvoiceTypeCode.text = "381"  # Credit note
                return invoice
            except Exception as e:
                    frappe.throw("error occured in simplified invoice typecode"+ str(e) )

def invoice_Typecode_Standard(invoice,sales_invoice_doc):
            try:
                    cbc_InvoiceTypeCode = ET.SubElement(invoice, "cbc:InvoiceTypeCode")
                    cbc_InvoiceTypeCode.set("name", "0100000") # Standard
                    if sales_invoice_doc.is_return == 0:
                        cbc_InvoiceTypeCode.text = "388"
                    elif sales_invoice_doc.is_return == 1:     # return items and simplified invoice
                        cbc_InvoiceTypeCode.text = "381" # Credit note
                    return invoice
            except Exception as e:
                    frappe.throw("Error in standard invoice type code: "+ str(e))
                    

































def doc_Reference_compliance(invoice,sales_invoice_doc,invoice_number, compliance_type):
            try:
                cbc_DocumentCurrencyCode = ET.SubElement(invoice, "cbc:DocumentCurrencyCode")
                cbc_DocumentCurrencyCode.text = sales_invoice_doc.currency
                cbc_TaxCurrencyCode = ET.SubElement(invoice, "cbc:TaxCurrencyCode")
                cbc_TaxCurrencyCode.text = sales_invoice_doc.currency
                
                if compliance_type == "3" or compliance_type == "4" or compliance_type == "5" or compliance_type == "6":
                
                    cac_BillingReference = ET.SubElement(invoice, "cac:BillingReference")
                    cac_InvoiceDocumentReference = ET.SubElement(cac_BillingReference, "cac:InvoiceDocumentReference")
                    cbc_ID13 = ET.SubElement(cac_InvoiceDocumentReference, "cbc:ID")
                    cbc_ID13.text = "6666666"  # field from return against invoice. 
                
                cac_AdditionalDocumentReference = ET.SubElement(invoice, "cac:AdditionalDocumentReference")
                cbc_ID_1 = ET.SubElement(cac_AdditionalDocumentReference, "cbc:ID")
                cbc_ID_1.text = "ICV"
                cbc_UUID_1 = ET.SubElement(cac_AdditionalDocumentReference, "cbc:UUID")
                cbc_UUID_1.text = str(get_ICV_code(invoice_number))
                return invoice  
            except Exception as e:
                    frappe.throw("Error occured in  reference doc" + str(e) )

def get_pih_for_company(pih_data, company_name):
                
                try:
                    for entry in pih_data.get("data", []):
                        if entry.get("company") == company_name:
                            return entry.get("pih")
                    frappe.throw("Error while retrieving  PIH of company for production:  " + str(e) )
                except Exception as e:
                        frappe.throw("Error in getting PIH of company for production:  " + str(e) )


def additional_Reference(invoice):
            try:
            #     settings=frappe.get_doc('Zatca setting')
            #     cac_AdditionalDocumentReference2 = ET.SubElement(invoice, "cac:AdditionalDocumentReference")
            #     cbc_ID_1_1 = ET.SubElement(cac_AdditionalDocumentReference2, "cbc:ID")
            #     cbc_ID_1_1.text = "PIH"
            #     cac_Attachment = ET.SubElement(cac_AdditionalDocumentReference2, "cac:Attachment")
            #     cbc_EmbeddedDocumentBinaryObject = ET.SubElement(cac_Attachment, "cbc:EmbeddedDocumentBinaryObject")
            #     cbc_EmbeddedDocumentBinaryObject.set("mimeCode", "text/plain")
                
            #     settings = frappe.get_doc('Zatca setting')
            #     company = settings.company
            #     company_name = frappe.db.get_value("Company", company, "abbr")
            #     pih_data_raw = settings.get("pih", "{}")
            #     pih_data = json.loads(pih_data_raw)
            #     pih = get_pih_for_company(pih_data, company_name)
                
            #     cbc_EmbeddedDocumentBinaryObject.text = pih
            #     # cbc_EmbeddedDocumentBinaryObject.text = "L0Awl814W4ycuFvjDVL/vIW08mNRNAwqfdlF5i/3dpU="
            # # QR CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------
            #     cac_AdditionalDocumentReference22 = ET.SubElement(invoice, "cac:AdditionalDocumentReference")
            #     cbc_ID_1_12 = ET.SubElement(cac_AdditionalDocumentReference22, "cbc:ID")
            #     cbc_ID_1_12.text = "QR"
            #     cac_Attachment22 = ET.SubElement(cac_AdditionalDocumentReference22, "cac:Attachment")
            #     cbc_EmbeddedDocumentBinaryObject22 = ET.SubElement(cac_Attachment22, "cbc:EmbeddedDocumentBinaryObject")
            #     cbc_EmbeddedDocumentBinaryObject22.set("mimeCode", "text/plain")
            #     cbc_EmbeddedDocumentBinaryObject22.text = "GsiuvGjvchjbFhibcDhjv1886G"
            # #END  QR CODE ------------------------------------------------------------------------------------------------------------------------------------------------------------------
                cac_sign = ET.SubElement(invoice, "cac:Signature")
                cbc_id_sign = ET.SubElement(cac_sign, "cbc:ID")
                cbc_method_sign = ET.SubElement(cac_sign, "cbc:SignatureMethod")
                cbc_id_sign.text = "urn:oasis:names:specification:ubl:signature:Invoice"
                cbc_method_sign.text = "urn:oasis:names:specification:ubl:dsig:enveloped:xades"
                return invoice
            except Exception as e:
                    frappe.throw("error occured in additional refrences" + str(e) )



def delivery_And_PaymentMeans(invoice,sales_invoice_doc, is_return):
            try:
                cac_Delivery = ET.SubElement(invoice, "cac:Delivery")
                cbc_ActualDeliveryDate = ET.SubElement(cac_Delivery, "cbc:ActualDeliveryDate")
                cbc_ActualDeliveryDate.text = str(sales_invoice_doc.due_date)
                cac_PaymentMeans = ET.SubElement(invoice, "cac:PaymentMeans")
                cbc_PaymentMeansCode = ET.SubElement(cac_PaymentMeans, "cbc:PaymentMeansCode")
                cbc_PaymentMeansCode.text = "30"
                
                if is_return == 1:
                    cbc_InstructionNote = ET.SubElement(cac_PaymentMeans, "cbc:InstructionNote")
                    cbc_InstructionNote.text = "Cancellation"    
                return invoice
            except Exception as e:
                    frappe.throw("Delivery and payment means failed"+ str(e) )
def delivery_And_PaymentMeans_for_Compliance(invoice,sales_invoice_doc, compliance_type):
            try:
                cac_Delivery = ET.SubElement(invoice, "cac:Delivery")
                cbc_ActualDeliveryDate = ET.SubElement(cac_Delivery, "cbc:ActualDeliveryDate")
                cbc_ActualDeliveryDate.text = str(sales_invoice_doc.due_date)
                cac_PaymentMeans = ET.SubElement(invoice, "cac:PaymentMeans")
                cbc_PaymentMeansCode = ET.SubElement(cac_PaymentMeans, "cbc:PaymentMeansCode")
                cbc_PaymentMeansCode.text = "30"
                
                if compliance_type == "3" or compliance_type == "4" or compliance_type == "5" or compliance_type == "6":
                    cbc_InstructionNote = ET.SubElement(cac_PaymentMeans, "cbc:InstructionNote")
                    cbc_InstructionNote.text = "Cancellation"    
                return invoice
            except Exception as e:
                    frappe.throw("Delivery and payment means failed"+ str(e) )
                                        
def billing_reference_for_credit_and_debit_note(invoice,sales_invoice_doc):
            try:
                #details of original invoice
                cac_BillingReference = ET.SubElement(invoice, "cac:BillingReference")
                cac_InvoiceDocumentReference = ET.SubElement(cac_BillingReference, "cac:InvoiceDocumentReference")
                cbc_ID13 = ET.SubElement(cac_InvoiceDocumentReference, "cbc:ID")
                cbc_ID13.text = sales_invoice_doc.return_against  # field from return against invoice. 
                
                return invoice
            except Exception as e:
                    frappe.throw("credit and debit note billing failed"+ str(e) )

def get_exemption_reason_map():
    return {
        "VATEX-SA-29": "Financial services mentioned in Article 29 of the VAT Regulations.",
        "VATEX-SA-29-7": "Life insurance services mentioned in Article 29 of the VAT Regulations.",
        "VATEX-SA-30": "Real estate transactions mentioned in Article 30 of the VAT Regulations.",
        "VATEX-SA-32": "Export of goods.",
        "VATEX-SA-33": "Export of services.",
        "VATEX-SA-34-1": "The international transport of Goods.",
        "VATEX-SA-34-2": "International transport of passengers.",
        "VATEX-SA-34-3": "Services directly connected and incidental to a Supply of international passenger transport.",
        "VATEX-SA-34-4": "Supply of a qualifying means of transport.",
        "VATEX-SA-34-5": "Any services relating to Goods or passenger transportation, as defined in article twenty five of these Regulations.",
        "VATEX-SA-35": "Medicines and medical equipment.",
        "VATEX-SA-36": "Qualifying metals.",
        "VATEX-SA-EDU": "Private education to citizen.",
        "VATEX-SA-HEA ": "Private healthcare to citizen.",
        "VATEX-SA-MLTRY": "Supply of qualified military goods",
        "VATEX-SA-OOS": "The reason is a free text, has to be provided by the taxpayer on case to case basis."
    
    }




