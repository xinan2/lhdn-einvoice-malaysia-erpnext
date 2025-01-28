
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
    }

});


