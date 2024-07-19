
frappe.ui.form.on("Lhdn Authorizations", {
    refresh: function(frm) {
                frm.add_custom_button(__("Generate Token"), function() {
                    frm.call({
                        // method:"myinvois.myinvois.myinvoissdkcode.myinvois_Call",
                        method:"myinvois.myinvois.sign_invoice.get_access_token",

                        args: {
                            "company_name": frm.doc.company_name
                        },
                        callback: function(response) {
                            if (response.message) {  
                                frappe.msgprint(response.message);
                                frm.reload_doc();
        
                            }
                            frm.reload_doc();
                        }
                        
                    
                    });
                    frm.reload_doc();
                });


                
         

           }
});
