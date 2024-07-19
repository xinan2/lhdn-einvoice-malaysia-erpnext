
import frappe

def on_submit(doc, method):
   
    for reference in doc.references:
        if reference.reference_doctype == "Sales Invoice":
            sales_invoice = frappe.get_doc("Sales Invoice", reference.reference_name)
            
            # Calculate the new paid amount
            sales_invoice.paid_amount = (sales_invoice.paid_amount or 0) + reference.allocated_amount
            print("Sales Paid Amount",sales_invoice.paid_amount)
            
            # Update the Sales Invoice
            sales_invoice.save(ignore_permissions=True)
            
            # Optionally, you can submit the Sales Invoice if it's not already submitted
            if sales_invoice.docstatus == 0:	
                sales_invoice.submit()
            
            # # Optionally, you can log the update
            # frappe.msgprint(f"Updated paid amount for Sales Invoice {sales_invoice.name}")
