/** @odoo-module */
import { registry } from "@web/core/registry"
import { loadJS, loadCSS } from "@web/core/assets"
import { useService } from "@web/core/utils/hooks"
const { Component, onWillStart, onMounted, useRef, useState } = owl
export class OwlMainDashboard extends Component {
    setup(){
        this.orm = useService("orm")
        this.notificationService = useService("notification");
        this.state = useState({
                monthly_data : [],
                mrp_plan_list:[],
                mrp_plan_product_data : [],
                weekly_mrp_plan_product_data : [],
                product_list: [],
            })

        onWillStart(async()=>{
            await loadJS("dw_mrp_plan/static/src/js/jquery.min.js")
            await loadCSS("dw_mrp_plan/static/src/css/bootstrap.min.css")
            await loadJS("dw_mrp_plan/static/src/js/bootstrap.bundle.min.js")
            await loadJS("dw_mrp_plan/static/src/js/popper.min.js")
            await loadJS("dw_mrp_plan/static/src/js/bootstrap.min.js")
            await loadJS("dw_mrp_plan/static/src/js/d3-collection.min.js")
            await loadCSS("dw_mrp_plan/static/src/css/tabulator.min.css")
            await loadJS("dw_mrp_plan/static/src/js/tabulator.min.js")
            await loadJS("dw_mrp_plan/static/src/js/select2.min.js")
            await loadCSS("dw_mrp_plan/static/src/css/select2.min.css")
            await loadJS("dw_mrp_plan/static/src/js/multiselect-dropdown.js")
            await loadCSS("dw_mrp_plan/static/src/css/docs.css")
            await loadCSS("dw_mrp_plan/static/src/components/tab/customCss.css")
        })

         onMounted(async ()=>{
            var cuurent_year = new Date().getFullYear()
            this.state.monthly_data = await this.get_mrp_plan_product_data(cuurent_year.toString().slice(2))
            var [original_data, data] = this.data_nest(this.state.monthly_data,'monthly')
            var monthly_tab
            var weekly_tab
            this.state.mrp_plan_product_data = original_data
            var monthly_columns = this.getTabCols(data)
            monthly_tab = this.setupTabulator(data,monthly_columns,"#tab");
            monthly_tab.on("tableBuilt", function() {
                monthly_tab.redraw();
            });
            //MRP Plan Select
            this.state.mrp_plan_list = await this.getMrpPlanList()
            var mrp_names_list = [...new Set(this.state.mrp_plan_list.map(item => [item.name,item.season_date]))]
            var selectMrpPlan= document.getElementById('select-mrp-plan');
            mrp_names_list.forEach(function(optionValue) {
              var option = this.addSelectOption(optionValue[0] +'/ ' +optionValue[1], optionValue[1])
              selectMrpPlan.appendChild(option);
            }.bind(this));
            const create_option = this.addSelectOption('Create MRP Plan...', 'createMrpPlan')
            selectMrpPlan.appendChild(create_option);
            $('#select-mrp-plan').change(function() {
                var selectedValues = $('#select-mrp-plan').val();
                if(selectedValues == 'createMrpPlan'){
                    console.log(".......... Creating MRP Plan ...........")
                    var company_data = this.getCompanyData()
                    company_data.then((result) => {
                        console.log("Company Data: ",result)
                        var selectCompanyMrpPlan= document.getElementById('select-mrp-plan-company');
                        result.forEach(function(optionValue) {
                            console.log("Options",optionValue)
                          var option = this.addSelectOption(optionValue['name'] , optionValue['id'])
                          selectCompanyMrpPlan.appendChild(option);
                        }.bind(this));
                        var company_id = $('#select-mrp-plan-company').val();
                        var sale_plan_data = this.getSalePlanData(company_id)
                        sale_plan_data.then((result) => {
                             var select_sale_plan = document.getElementById("select-mrp-sale-plan");
                             select_sale_plan.innerHTML = "";
                             result.forEach(function(optionValue) {
                                 var option = this.addSelectOption(optionValue['name'] , optionValue['id'])
                                 select_sale_plan.appendChild(option);
                                 }.bind(this));
                            }).catch((error) => {
                                console.error(error); // Handle any errors
                        });

                        var season_data = this.generateSeasonData()
                        console.log("DATA 88",season_data)
                        var select_season_plan = document.getElementById("select-mrp-season-plan");
                        season_data.forEach(function(optionValue) {
                             var option = this.addSelectOption(optionValue[1] , optionValue[0])
                             select_season_plan.appendChild(option);
                        }.bind(this));



                    }).catch((error) => {
                        console.error(error); // Handle any errors
                    });
                    $('#createMrpPlanModel').modal('show');
                }else{
                    var res = this.get_mrp_plan_product_data(selectedValues)
                    res.then((result) => {
                        this.state.monthly_data = result
                        var [original_data, data] = this.data_nest(result,'monthly')
                        this.state.mrp_plan_product_data = original_data
                        var filtred_data = data.filter(function(dict) {
                            return selectedValues.includes(dict['Product']);
                        });
                        var monthly_columns = this.getTabCols(data)
                        monthly_tab.setData(data);
                        monthly_tab.setColumns(monthly_columns);
                    }).catch((error) => {
                        console.error(error);
                    });
                }

            }.bind(this));

            $('#select-mrp-plan-company').change(function () {
                var selectedValues = $('#select-mrp-plan-company').val();
                var company_id = $('#select-mrp-plan-company').val();
                var sale_plan_data = this.getSalePlanData(company_id)
                sale_plan_data.then((result) => {
                     var select_sale_plan = document.getElementById("select-mrp-sale-plan");
                     select_sale_plan.innerHTML = "";
                     result.forEach(function(optionValue) {
                         var option = this.addSelectOption(optionValue['name'] , optionValue['id'])
                         select_sale_plan.appendChild(option);
                         }.bind(this));
                    }).catch((error) => {
                        console.error(error);
                });
            }.bind(this));

            document.getElementById("saveMrpPlanButton").addEventListener("click", function () {
                    var plan_name = $('#mrp-plan-name').val();
                    var plan_season = $('#select-mrp-season-plan').val();
                    var plan_company = $('#select-mrp-plan-company').val();
                    var plan_sale_plan = $('#select-mrp-sale-plan').val();

                    console.log('plan_name',plan_name)
                    console.log('plan_season',plan_season)
                    console.log('plan_company',plan_company)
                    console.log('plan_sale_plan',plan_sale_plan)
                    var new_mrp_plan = this.createMrpPlan(plan_name, plan_season, plan_company, plan_sale_plan)
                    new_mrp_plan.then((result) => {
                        var mrp_plan_notif = this.notificationService.add("MRP Plan "+plan_name+" Successfully Created", {
                          title: "Create MRP Plan",
                          type: "success"
                        });
                        setTimeout(mrp_plan_notif, 2000);
                    }).catch((error) => {
                         var mrp_plan_notif = this.notificationService.add("MRP Plan "+plan_name+" Cant be created, Please contact your system administrator", {
                          title: "Create MRP Plan",
                          type: "danger"
                        });
                        setTimeout(mrp_plan_notif, 2000);
                    });

                }.bind(this));

            monthly_tab.on("headerDblClick", function(e, column){
                $('#tableBody').html('');
                $('#tableHead').html('');
                var date = new Date(column.getField())
                var prod = []
                var start_date = this.formatDate(column.getField(),-1)
                var end_date = this.getLastDayOfMonth(start_date)
                monthly_tab.getData().forEach(function(row) {
                    prod.push(row['Product']);
                });
                var prod_ids = this.getValueBasedOnKey(prod,this.state.mrp_plan_product_data, 'product', 'productID')
                var weekly_data =  this.getWeeklyPlan(prod_ids, start_date, end_date)// check end date return wrong day (29 intead of 31 for dec)
                weekly_data.then((result) => {
                    var [main_weekly_data,tab_data] = this.data_nest(result,'weekly')
                    this.state.weekly_mrp_plan_product_data = main_weekly_data
                    let modal = document.getElementById("WeeklyPlaModel");
                    this.addTabtToModal();
                    var weekly_columns = this.getTabCols(tab_data,'weekly')
                    weekly_tab = this.setupTabulator(tab_data,weekly_columns,"#WeeklyTab");
                }).catch((error) => {
                    console.error(error); // Handle any errors
                });
                $('#WeeklyPlaModel').modal('show');
            }.bind(this));
        })
    }

    addTabtToModal() {
        // Create a div element with class and id
        let tab = document.createElement('div');
        tab.className = 'table table-hover'; // Add class
        tab.id = 'WeeklyTab'; // Add id
        let modalBody = document.getElementById('WeeklyPlanmodalBody');
        modalBody.appendChild(tab);
    }

    updateObjectById(proxyArray, id, key, value) {
        return proxyArray.map(obj => {
            if (obj.id === id) {
                return { ...obj, [key]: value };
            } else {
                return obj;
            }
        });
    }

    async getWeeklyPlan(prod_list_ids, start_date, end_date){
        var data =  this.orm.searchRead("product.mrp.plan.weekly",
                        [['product_id.id','in',prod_list_ids],
                        ['date', '>=', start_date],['date', '<=', end_date]],
                        ['quantity','date','product_id','expected_start_quantity','sale_planned_quantity','lot_size','expected_final_quantity','sale_capacity','autonomy','pdp_validation'])
        var res = []
        await data.then(result => {
             res = result
        }).catch(error => {
            console.error(error);
        });
        return res
    }

    getTabCols(data,type='monthly'){
        if (data.length > 0){
            var cols = Object.keys(data[0])
            var columns = Object.keys(data[0]).map(key => {
                if (type == 'monthly'){
                    if (key === 'Product' ){
                        return{
                            title: key,
                            field: key,
                            headerFilter:true,
                            formatter: this.actionButtonFormatter.bind(this)
                        }
                    }else{
                        return{
                            title: key,
                            field: key,
                            editor: 'number',
                            cellEdited: this.monthlycellEdited.bind(this),
                        }
                    }
                }else{
                    if (key === 'Product' ){
                        return{
                            title: key,
                            field: key,
                            headerFilter:true,
                            formatter: this.weeklyActionButtonFormatter.bind(this)
                        }
                    }else{
                        return{
                            title: key,
                            field: key,
                            editor: 'number',
                            cellEdited: this.weeklyCellEdited.bind(this),
                        }
                    }
                }

            });
            return columns
        }else{
             return []
        }
    }

    actionButtonFormatter(cell, formatterParams, onRendered) {
        // Create the split cell container
        var container = document.createElement('div');
        container.classList.add('split-cell');
        // Create the cell value container
        var valueContainer = document.createElement('div');
        valueContainer.classList.add('cell-value');
        valueContainer.textContent = cell.getValue();
        // Create the button container
        var buttonContainer = document.createElement('div');
        buttonContainer.classList.add('button-container');
        // Create the button element
        var button = document.createElement('button');
        button.innerHTML = '&#9776';
        button.dataset.toggle = "modal"
        button.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent cell click event from triggering
            var cellValue = cell.getValue();
            var proxy_details = this.state.mrp_plan_product_data.filter(obj => obj['product'] === cellValue)
            $('#tableBody').html('');
            $('#tableHead').html('');
            this.addTableHead()
            const list_details = proxy_details.map(proxyObject => {
                const newObj = {};
                for (let key of Object.keys(proxyObject)) {
                    newObj[key] = proxyObject[key];
                }
                this.addTableRow(newObj['id'],this.formatDate(newObj['date']), newObj['expected_final_quantity'], newObj['expected_start_quantity'], newObj['lot_size']
                                , newObj['quantity'], newObj['sale_capacity'], newObj['sale_planned_quantity'])
                return newObj;
            });
            $('#tableTitle').text(list_details[0]['product'])
            $('#PDPValidationModel').modal('show');
            document.getElementById("checkAll").addEventListener("change", function () {
                var checkboxes = document.querySelectorAll(".checkBox");
                checkboxes.forEach(function (checkbox) {
                    checkbox.checked = this.checked;
                }.bind(this));
            });
            document.getElementById("save").addEventListener("click", function () {
                    var checkboxes = document.querySelectorAll(".checkBox");
                    var checkedValues = [];
                    checkboxes.forEach(function(checkbox) {
                            if (checkbox.checked) {
                                checkedValues.push(checkbox.value);
                            }
                        }.bind(this));
                        var close = this.notificationService.add("All Selected Records Has Been Updated Successfully", {
                              title: "Success",
                              type: "success"
                            });
                            setTimeout(close, 2000);
                    this.validateDates(checkedValues,'monthly')
                }.bind(this));
            }.bind(this));
        // Append the value and button containers to the split cell container
        container.appendChild(valueContainer);
        buttonContainer.appendChild(button);
        container.appendChild(buttonContainer);
        return container;
    }

    weeklyActionButtonFormatter(cell, formatterParams, onRendered) {
        // Create the split cell container
        var container = document.createElement('div');
        container.classList.add('split-cell');
        // Create the cell value container
        var valueContainer = document.createElement('div');
        valueContainer.classList.add('cell-value');
        valueContainer.textContent = cell.getValue();
        // Create the button container
        var buttonContainer = document.createElement('div');
        buttonContainer.classList.add('button-container');
        // Create the button element
        var button = document.createElement('button');
        button.innerHTML = '&#9776';
        button.dataset.toggle = "modal"
        button.addEventListener('click', function(e) {
            e.stopPropagation(); // Prevent cell click event from triggering
            var cellValue = cell.getValue();
            var proxy_details = this.state.weekly_mrp_plan_product_data.filter(obj => obj['product'] === cellValue)
            $('#tableBody').html('');
            $('#tableHead').html('');
            this.addTableHead()
            const list_details = proxy_details.map(proxyObject => {
                const newObj = {};
                for (let key of Object.keys(proxyObject)) {
                    newObj[key] = proxyObject[key];
                }
                this.addTableRow(newObj['id'],newObj['date'], newObj['expected_final_quantity'], newObj['expected_start_quantity'], newObj['lot_size']
                                , newObj['quantity'], newObj['sale_capacity'], newObj['sale_planned_quantity'])
                return newObj;
            });
            $('#tableTitle').text(list_details[0]['product'] + "/ Weekly Plan For: "+this.formatDate(list_details[0]['date']))
            $('#PDPValidationModel').modal('show');
            document.getElementById("checkAll").addEventListener("change", function () {
                var checkboxes = document.querySelectorAll(".checkBox");
                checkboxes.forEach(function (checkbox) {
                    checkbox.checked = this.checked;
                }.bind(this));
            });
            document.getElementById("save").addEventListener("click", function () {
                    var checkboxes = document.querySelectorAll(".checkBox");
                    var checkedValues = [];
                    checkboxes.forEach(function(checkbox) {
                            if (checkbox.checked) {
                                checkedValues.push(checkbox.value);
                            }
                        }.bind(this));
                    this.validateDates(checkedValues,'weekly')
                    this.notificationService.add("All Selected Records Has Been Updated Successfully", {
                      title: "Success",
                      type: "success"
                    });
                }.bind(this));
            }.bind(this));
        // Append the value and button containers to the split cell container
        container.appendChild(valueContainer);
        buttonContainer.appendChild(button);
        container.appendChild(buttonContainer);
        return container;
    }

    async getMrpPlanList(){
        var data =  this.orm.searchRead("mrp.plan",[[1,'=',1]],['name','season_date'])
        var res = []
        await data.then(result => {
             res = result
        }).catch(error => {
            console.error(error);
        });
        return res
    }

    validateDates(ids_list,type){
        ids_list.forEach((id,step) => {
            (function(recordId,step) {
                setTimeout(function() {
                    if (type == 'monthly'){
                        this.orm.write('product.mrp.plan', [parseInt(id)], {
                            ['pdp_validation']: true
                            });
                        this.state.mrp_plan_product_data = this.updateObjectById(this.state.mrp_plan_product_data , parseInt(id), 'pdp_validation', true)
                    }else{
                        this.orm.write('product.mrp.plan.weekly', [parseInt(id)], {
                            ['pdp_validation']: true
                            });
                        this.state.weekly_mrp_plan_product_data = this.updateObjectById(this.state.weekly_mrp_plan_product_data , parseInt(id), 'pdp_validation', true)
                    }
                }.bind(this), 200 * step);
            }.bind(this))(id,step);
        });
    }

    addTableRow(id,Date, expected_final_quantit, expected_start_quantity,lot_size,quantity
            , sale_capacity, sale_planned_quantity) {
        var newRow = $('<tr>');
        newRow.append('<td> <input type="checkbox" value = "'+ id +'" class="checkBox"/> </td>');
        newRow.append('<td>' + Date + '</td>');
        newRow.append('<td>' + expected_final_quantit + '</td>');
        newRow.append('<td>' + expected_start_quantity + '</td>');
        newRow.append('<td>' + lot_size + '</td>');
        newRow.append('<td> <span class="badge bg-primary"> ' + quantity + '</span> </td>');
        newRow.append('<td>' + sale_capacity + '</td>');
        newRow.append('<td>' + sale_planned_quantity + '</td>');
        $('#tableBody').append(newRow);
    }

    addTableHead(){
        var head = $('<tr>');
        head.append('<th scope="col"><input type="checkbox" id="checkAll"/></th>');
        head.append('<th scope="col">Date</th>');
        head.append('<th scope="col">Expected Final Quantit</th>');
        head.append('<th scope="col">Expected Start Quantity</th>');
        head.append('<th scope="col">Lot Size</th>');
        head.append('<th scope="col">Quantity</th>');
        head.append('<th scope="col">Sale Capacity</th>');
        head.append('<th scope="col">Sale Planned Quantity</th>');
        $('#tableHead').append(head);
    }

    formatDate(dateString,type=1) {
        if(type == 1){
            const date = new Date(dateString);
            const options = { year: 'numeric', month: 'short' };
            return date.toLocaleDateString('en-US', options);
        }else{
            var parts = dateString.split(' ');
            var month = parts[0];
            var year = parseInt(parts[1]);
            var monthNumber = new Date(Date.parse(month + " 1, 2020")).getMonth() + 1;
            var formattedDate = year + '-' + ('0' + monthNumber).slice(-2) + '-01';
            return formattedDate;
        }
    }

    getLastDayOfMonth(dateString) {
        // Parse the date string
        let parts = dateString.split('-');
        let year = parseInt(parts[0]);
        let month = parseInt(parts[1]) - 1; // Adjust month to zero-based index
        let day = parseInt(parts[2]);
        let date = new Date(year, month, day);
        date.setDate(0);
        date.setMonth(date.getMonth() + 1);
        let lastDayOfMonth = date.toISOString().slice(0, 10);
        return lastDayOfMonth;
    }

     setupTabulator(data,columns,id){
        var table = new Tabulator(id, {
                            height: "auto",
                            layout:"fitColumns",
                            data:data,
                            placeholder:"Please Select MRP Plan To Display",
                            pagination:"local",
                            paginationSize:6,
                            paginationSizeSelector:[3, 5, 8, 12],
                            movableColumns:true,
                            paginationCounter:"rows",
                            columns: columns,
                        });
        return table
    }

    searchItem(proxyList, key1, value1, key2, value2, returnField) {
        for (let item of proxyList) {
            if (item[key1] === value1 && item[key2] === value2) {
                return item[returnField];
            }
        }
        return null;
    }

    getValueBasedOnKey(prod_list,proxyList, otherKey, targetKey) {
        var ids = []
        for (let prod of prod_list) {
            var proxy = proxyList.find(function(item) {
                return item[otherKey] === prod;
            });
            if (proxy) {
                ids.push(proxy[targetKey]);
            }
        }
        return ids;
    }

    async monthlycellEdited(cell){
        const editedValue = cell.getValue();
        const columnField = cell.getField();
        const prod = cell.getData()['Product']
        var pdp_validated = this.searchItem(this.state.mrp_plan_product_data, 'date', this.formatDate(columnField,-1), 'product', prod, 'pdp_validation')
        if(pdp_validated === true){
             cell.getElement().style.backgroundColor = "#ADD8E6";
             cell.restoreOldValue();
        }else{
            var record_id_to_update = this.searchItem(this.state.mrp_plan_product_data, 'date', this.formatDate(columnField,-1), 'product', prod, 'id')
            cell.getElement().setAttribute("contenteditable", false);
            try {
                var prod_name = cell.getData()['Product']
                await this.orm.write('product.mrp.plan', [record_id_to_update], {
                    ['quantity']: editedValue
                });
                console.log('Field value updated successfully');
                this.state.mrp_plan_product_data = this.updateObjectById(this.state.mrp_plan_product_data , record_id_to_update, 'quantity', editedValue)
            } catch (error) {
                console.error('Error updating field value:', error);
            }
        }
    }

    async weeklyCellEdited(cell){
        const editedValue = cell.getValue();
        const columnField = cell.getField();
        const prod = cell.getData()['Product']
        var pdp_validated = this.searchItem(this.state.weekly_mrp_plan_product_data, 'date', columnField, 'product', prod, 'pdp_validation')
        if(pdp_validated === true){
             cell.getElement().style.backgroundColor = "#ADD8E6";
             cell.restoreOldValue();
        }else{
            var record_id_to_update = this.searchItem(this.state.weekly_mrp_plan_product_data, 'date', columnField, 'product', prod, 'id')
            try {
                var prod_name = cell.getData()['Product']
                await this.orm.write('product.mrp.plan.weekly', [record_id_to_update], {
                    ['quantity']: editedValue
                });
                this.state.weekly_mrp_plan_product_data = this.updateObjectById(this.state.weekly_mrp_plan_product_data , record_id_to_update, 'quantity', editedValue)
                console.log('Field value updated successfully');
            } catch (error) {
                console.error('Error updating field value:', error);
            }
        }
    }

    async get_mrp_plan_product_data(year) {
        var data =  this.orm.searchRead("product.mrp.plan",[[1,'=',1],['product_plan_id.plan_id.season_date','=',year]],['quantity','date','product_id','expected_start_quantity','sale_planned_quantity','lot_size','expected_final_quantity','sale_capacity','autonomy','pdp_validation'])
        var res = []
        await data.then(result => {
             res = result
        }).catch(error => {
            console.error(error);
        });
        return res
    }


    data_nest(data,type){
        if(data.length === 0 ){
            return [[],[]]
        }else{
            data.forEach(dict => {
                for (const key in dict) {
                    dict['product'] = dict['product_id'][1]
                    dict['productID'] = dict['product_id'][0]
                }
            });
            const groupedData = d3.nest()
                .key(d => d['product']) // Group by product
                .entries(data);
            var res = []
            var r = {}
            groupedData.forEach(row => {
                r["Product"] = row.key
                row.values.forEach(row1 => {
                    if (type == 'monthly'){
                        r[this.formatDate(row1["date"])] =  row1["quantity"]
                    }else{
                        r[row1["date"]] =  row1["quantity"]
                    }
                });
                res.push(r)
                r = {}
            });
            return [data, res]
        }
    }

    addSelectOption(text, value){
        var option = document.createElement('option');
        option.text = text;
        option.value = value; // Set both text and value to the same value
        return option
    }

    async getSalePlanData(company_id) {
        var data =  this.orm.searchRead("sale.plan",['|',['company_id.id','=', company_id],['company_id','=',false]],['id', 'name'])
        var res = []
        await data.then(result => {
             res = result
        }).catch(error => {
            console.error(error);
        });
        return res
    }

    async getCompanyData() {
        var data =  this.orm.searchRead("res.company",[[1,'=',1]],['id', 'name'])
        var res = []
        await data.then(result => {
             res = result
        }).catch(error => {
            console.error(error);
        });
        return res
    }

    generateSeasonData(){
        var cnt = 10;
        var list1 = [];
        var today = new Date().getFullYear();
        for (let i = 2010; i < today + 5; i++) {
            list1.push([cnt.toString(), i.toString()]);
            cnt = cnt + 1;
        }
        return list1
    }

    createMrpPlan(plan_name, plan_season, plan_company_id, plan_sale_plan_id){
         var new_mrp_plan = this.orm.create('mrp.plan', [{
                            'name': plan_name,
                            'season_date': plan_season,
                            'sale_plan_id': plan_sale_plan_id,
                            'company_id': plan_company_id,
                            }]);
        return new_mrp_plan
    }

}
OwlMainDashboard.template = "owl.OwlMainDashboard"
registry.category("actions").add("owl.main_dashboard", OwlMainDashboard)