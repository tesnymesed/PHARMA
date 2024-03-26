/** @odoo-module */
import { registry } from "@web/core/registry"
import { loadJS, loadCSS } from "@web/core/assets"
import { useService } from "@web/core/utils/hooks"
const { Component, onWillStart, onMounted, useRef, useState } = owl

export class OwlMainDashboard extends Component {
    setup(){
        this.orm = useService("orm")
        onWillStart(async()=>{
            await loadJS("https://unpkg.com/tabulator-tables@4.1.4/dist/js/tabulator.min.js")
            await loadJS("https://cdn.jsdelivr.net/npm/d3-collection@1.0.7/dist/d3-collection.min.js")
            await loadCSS("https://unpkg.com/tabulator-tables@4.1.4/dist/css/tabulator.min.css")
        })
          this.state = useState({
                original_data : []
            })
         onMounted(async ()=>{
            var [original_data, data] = await this.data_nest()
            this.state.original_data = original_data
            var cols = Object.keys(data[0])
            var columns = Object.keys(data[0]).map(key => ({
                title: key,
                field: key,
                editor: 'number',
                cellEdited: this.cellEdited.bind(this)
            }));
            await this.setupTabulator(data,columns);
        })


    }
async setupTabulator(data,columns){
    var table = new Tabulator("#tab", {
                        height:"311px",
                        layout:"fitColumns",
                        resizableColumnFit:true,
                        data:data,
                        columns: columns,
                    });
    table.redraw();
}
searchItem(proxyList, key1, value1, key2, value2) {
    for (let item of proxyList) {
        if (item[key1] === value1 && item[key2] === value2) {
            return item['id'];
        }
    }
    return null;
}
async cellEdited(cell){
    const editedValue = cell.getValue();
    const columnField = cell.getField();
    const prod = cell.getData()['Product']
    var record_id_to_update = this.searchItem(this.state.original_data, 'date', columnField, 'product', prod)
    try {
            var prod_name = cell.getData()['Product']
            await this.orm.write('product.mrp.plan', [record_id_to_update], {
                ['quantity']: editedValue
            });
            console.log('Field value updated successfully');
        } catch (error) {
            console.error('Error updating field value:', error);
        }
}

 async get_data() {
    var data =  this.orm.searchRead("product.mrp.plan",[[1,'=',1]],['quantity','date','product_id'])
    var res = []
    await data.then(result => {
         res = result
    }).catch(error => {
        console.error(error);
    });
    return res
    }


async data_nest(){
        var data = await this.get_data()
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
                r[row1["date"]] =  row1["quantity"]
            });
            res.push(r)
            r = {}
        });
                return [data, res]
    }
}
OwlMainDashboard.template = "owl.OwlMainDashboard"
registry.category("actions").add("owl.main_dashboard", OwlMainDashboard)