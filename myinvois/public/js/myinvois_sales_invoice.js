
frappe.ui.form.on("Sales Invoice", {
    refresh: function(frm) {
                frm.add_custom_button(__("Send e-invoice"), function() {
                    frm.call({
                        // method:"myinvois.myinvois.myinvoissdkcode.myinvois_Call",
                        // method:"myinvois.myinvois.sign_invoice.myinvois_Call",
                        method:"myinvois.myinvois.sign_invoice.lhdn_Background",
                        
                        
                        args: {
                            "invoice_number": frm.doc.name,

                        },
                        // args: {
                        //     "invoice_number": frm.doc.name,
                        //     "company_name" : frm.doc.company_name,
                        //     "compliance_type": "1"
                        // },
                        callback: function(response) {
                            if (response.message) {  
                                frappe.msgprint(response.message);
                                frm.reload_doc();
        
                            }
                            frm.reload_doc();
                        }
                        
                    
                    });
                    frm.reload_doc();
                }, __("LHDN E-Invois"));
                frm.add_custom_button(__("Cancel e-invoice"), function() { 
                    frappe.call({
                       method:"myinvois.myinvois.sign_invoice.lhdn_Cancel_Background",
                       args:{
                            "uuid": frm.doc.custom_uuid,
                            "invoice_number":frm.doc.name
                       },
                       callback: function(response){
                        if (response.message) {  
                            frappe.msgprint(response.message);
                            frm.reload_doc();
    
                        }
                        frm.reload_doc();
                       }
                    });
            }, __("LHDN E-Invois"));
            

    },
    custom_refresh_status:function(frm){
        frm.call({
            // method:"myinvois.myinvois.myinvoissdkcode.myinvois_Call",
            // method:"myinvois.myinvois.sign_invoice.myinvois_Call",
            method:"myinvois.myinvois.sign_invoice.refresh_doc_status",
            
            
            args: {
                "uuid": frm.doc.custom_uuid,
                "invoice_number":frm.doc.name

            },
            // args: {
            //     "invoice_number": frm.doc.name,
            //     "company_name" : frm.doc.company_name,
            //     "compliance_type": "1"
            // },
            callback: function(response) {
                if (response.message) {  
                    frappe.msgprint(response.message);
                    frm.reload_doc();

                }
                frm.reload_doc();
            }
            
        
        });
        frm.reload_doc();
    },
    setup: function(frm) {
        frm.fields_dict["items"].grid.get_field("custom_exemption_against_item_tax_template").get_query = function(doc, cdt, cdn) {
            return {
                filters: {
                    company: frm.doc.company,
                    custom_lhdn_tax_type_code: ["!=", "E"] // Exclude "Tax Exemption"

                }
            };
        };

        // frm.set_query("taxes_and_charges", function() {
        //     return {
        //         filters: {
        //             custom_lhdn_tax_type_code: ["!=", "E"] // Exclude "Tax Exemption"
        //         }
        //     };
        // });
    },
    before_save: function(frm) {
        
        if (frm.doc.is_return === 1 && frm.doc.custom_einvoice_type != "Credit Note") {
            console.log("enter in this lock");
            
           frm.set_value("custom_einvoice_type", "Credit Note");
           
        }

    },

});


frappe.ui.form.on("Sales Invoice Item", {
    custom_exemption_against_item_tax_template: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
    
        if (row.custom_exemption_against_item_tax_template) {
            frappe.call({
                method: "frappe.client.get",
                args: {
                    doctype: "Item Tax Template",
                    name: row.custom_exemption_against_item_tax_template
                },
                callback: function(r) {
                    if (r.message && r.message.taxes) {
                        let tax_rate = 0;
    
                        // Assuming you want the first available tax rate
                        if (r.message.taxes.length > 0) {
                            tax_rate = r.message.taxes[0].tax_rate;
                        }
    
                        frappe.model.set_value(cdt, cdn, "custom_exemption_against_tax_rate", tax_rate);
                        frappe.model.set_value(cdt, cdn, "custom_exemption_against_tax_rate", tax_rate);

                    }
                }
            });
        }
    }


});


