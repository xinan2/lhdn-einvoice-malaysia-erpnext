frappe.ui.form.on("Purchase Invoice",{
    refresh: function(frm) {
            frm.add_custom_button(__("Send E-Invoice"), function() {
                    frm.call({
                        method:"myinvois.myinvois.sign_purchase.lhdn_Background",

                        args: {
                            "invoice_number": frm.doc.name,
                        },
                        callback: function(response) {
                            if (response.message) {  
                                frappe.msgprint(response.message);
                                frm.reload_doc();
                            }
                            frm.reload_doc();
                        }
                    });
                }, __("LHDN E-Invois"));
                
            // frm.add_custom_button(__("Cancel E-Invoice"), function() { 
            //         frappe.call({
            //            method:"myinvois.myinvois.sign_invoice.lhdn_Cancel_Background",
            //            args:{
            //                 "uuid": frm.doc.custom_uuid,
            //                 "invoice_number":frm.doc.name
            //            },
            //            callback: function(response){
            //             if (response.message) {  
            //                 frappe.msgprint(response.message);
            //                 frm.reload_doc();
            //             }
            //             frm.reload_doc();
            //            }
            //         });
            // }, __("LHDN E-Invois"));

            frm.set_query("custom_einvoice_type", function() {
                return {
                    filters: {
                        "custom_doctype": ["=", "Purchase Invoice"] 
                    }
                };
            });
    },
    company: function(frm) {
        if (!frm.doc.company) return;

        frappe.db.get_doc("Company", frm.doc.company)
            .then(function(company) {
                frm.set_value("company_tax_id", company.tax_id || "");
            })
            .catch(function(error) {
                frappe.msgprint(__("Failed to fetch Company details: ") + error.message);
            });

        
    },
    custom_refresh_status:function(frm){
        frm.call({
            // method:"myinvois.myinvois.myinvoissdkcode.myinvois_Call",
            // method:"myinvois.myinvois.sign_invoice.myinvois_Call",
            method:"myinvois.myinvois.sign_purchase.refresh_doc_status",
            
            
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
        }



});

frappe.ui.form.on("Purchase Invoice Item", {

    item_tax_template: function(frm,cdt,cdn){
        var  row = locals[cdt][cdn];
        if (row.item_tax_template) {
            frappe.db.get_value("Item Tax Template", row.item_tax_template,["custom_lhdn_tax_type_description","custom_lhdn_tax_type_code"])
            .then(r => {
                if(r.message) {
                    if (r.message.custom_lhdn_tax_type_description){
                        console.log("enter in lhdn type");
                        frappe.model.set_value(cdt, cdn, "custom_lhdn_tax_type", r.message.custom_lhdn_tax_type_description);
                    }

                    if (r.message.custom_lhdn_tax_type_code) {
                        console.log("enter in lhdn type code");
                        frappe.model.set_value(cdt, cdn, "custom_lhdn_tax_type_code", r.message.custom_lhdn_tax_type_code);
                    }


                }
            })
        }
    },
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
                        row.custom_exemption_against_tax_rate = r.message.taxes[0].tax_rate;
                        row.custom__tax_type_ = r.message.custom_lhdn_tax_type_description;
                        row.custom_tax_code = r.message.custom_lhdn_tax_type_code;
                        frm.refresh_field("items");
                    }
                }
            });
        } else {
            row.custom_exemption_against_item_tax = 0;
            row.custom__tax_type_ = "";
            row.custom_tax_code = "";
            frm.refresh_field("items");
        }
    }

});