/** @odoo-module */
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
const { Component, onWillStart, onMounted, useRef, useState } = owl;
export class OwlMainDashboard extends Component {
  setup() {
    this.orm = useService("orm");
    this.notificationService = useService("notification");
    this.state = useState({
      monthly_data: [],
      mrp_plan_list: [],
      mrp_plan_product_data: [],
      weekly_mrp_plan_product_data: [],
      product_list: [],
    });

    onMounted(async () => {
      $(".select2").select2({
        closeOnSelect: false,
      });
      //MRP Plan Select
      this.state.mrp_plan_list = await this.getMrpPlanList();
      var mrp_names_list = [
        ...new Set(
          this.state.mrp_plan_list.map((item) => [
            item.name,
            item.season_date,
            item.id,
          ])
        ),
      ];
      var selectMrpPlan = document.getElementById("select-mrp-plan");
      mrp_names_list.forEach(
        function (optionValue) {
          var option = this.addSelectOption(
            optionValue[0] + "/ " + optionValue[1],
            optionValue[2]
          );
          selectMrpPlan.appendChild(option);
        }.bind(this)
      );
      const create_option = this.addSelectOption(
        "Create MRP Plan...",
        "createMrpPlan"
      );
      selectMrpPlan.appendChild(create_option);

      //Load tab data
      var selected_plan_id = $("#select-mrp-plan").val();
      // var cuurent_year = new Date().getFullYear()
      this.state.monthly_data = await this.get_mrp_plan_product_data(
        "",
        selected_plan_id == "createMrpPlan" ? -1 : selected_plan_id
      );
      var [original_data, data] = this.data_nest(
        this.state.monthly_data,
        "monthly"
      );
      var monthly_tab;
      var weekly_tab;
      this.state.mrp_plan_product_data = original_data;
      var monthly_columns = this.getTabCols(data);
      monthly_tab = this.setupTabulator(data, monthly_columns, "#tab");
      monthly_tab.on("tableBuilt", function () {
        monthly_tab.redraw();
      });

      $("#create-plan").click(
        function () {
          this.btnCreateMrpPla();
        }.bind(this)
      );

      $("#select-mrp-plan").change(
        function () {
          var selectedValues = $("#select-mrp-plan").val();
          if (selectedValues == "createMrpPlan") {
            this.btnCreateMrpPla();
          } else {
            var res = this.get_mrp_plan_product_data("", selectedValues);
            res
              .then((result) => {
                this.state.monthly_data = result;
                var [original_data, data] = this.data_nest(result, "monthly");
                this.state.mrp_plan_product_data = original_data;
                var filtred_data = data.filter(function (dict) {
                  return selectedValues.includes(dict["Product"]);
                });
                var monthly_columns = this.getTabCols(data);
                monthly_tab.setData(data);
                monthly_tab.setColumns(monthly_columns);
              })
              .catch((error) => {
                console.error(error);
              });
          }
        }.bind(this)
      );

      $("#createMrpPlanModel").on("shown.bs.modal", function () {
        $(".date-own").datepicker({
          container: "#createMrpPlanModalBody",
          autoclose: true,
          minViewMode: 2,
          format: "yyyy",
        });
      });

      $("#select-mrp-plan-company").change(
        function () {
          var selectedValues = $("#select-mrp-plan-company").val();
          var company_id = $("#select-mrp-plan-company").val();
          var sale_plan_data = this.getSalePlanData(company_id);
          sale_plan_data
            .then((result) => {
              var select_sale_plan = document.getElementById(
                "select-mrp-sale-plan"
              );
              select_sale_plan.innerHTML = "";
              result.forEach(
                function (optionValue) {
                  var option = this.addSelectOption(
                    optionValue["name"],
                    optionValue["id"]
                  );
                  select_sale_plan.appendChild(option);
                }.bind(this)
              );
              var df_option = this.addSelectOption("Empty", "");
              select_sale_plan.appendChild(df_option);
            })
            .catch((error) => {
              console.error(error);
            });
        }.bind(this)
      );

      $("#saveMrpPlanButton")
        .off("click")
        .on(
          "click",
          function () {
            var plan_name = $("#mrp-plan-name").val();
            var plan_season = $("#select-mrp-season-plan").val();
            var plan_company = $("#select-mrp-plan-company").val();
            var plan_sale_plan = $("#select-mrp-sale-plan").val();
            var new_mrp_plan = this.createMrpPlan(
              plan_name,
              plan_season,
              plan_company,
              plan_sale_plan
            );
            new_mrp_plan
              .then((result) => {
                var mrp_plan_notif = this.notificationService.add(
                  "MRP Plan " + plan_name + " Successfully Created",
                  {
                    title: "Create MRP Plan",
                    type: "success",
                  }
                );
                setTimeout(mrp_plan_notif, 2000);
                setTimeout(function () {
                  location.reload(true);
                }, 2000);
                $("#createMrpPlanModel").modal("hide");
              })
              .catch((error) => {
                var mrp_plan_notif = this.notificationService.add(
                  "MRP Plan " +
                    plan_name +
                    " Cant be created, Please check Season Date (must be unique within the same company) or contact your system administrator",
                  {
                    title: "Create MRP Plan",
                    type: "danger",
                  }
                );
                setTimeout(mrp_plan_notif, 5000);
              });
          }.bind(this)
        );

      document.getElementById("add-products").addEventListener(
        "click",
        function () {
          var mrp_plan_id = $("#select-mrp-plan").val();
          var row_id = 1;
          var products = this.orm.searchRead(
            "product.product",
            [
              ["product_tmpl_id.categ_id.is_final_product", "=", true],
              ["product_tmpl_id.bom_ids", "!=", false],
            ],
            ["id", "display_name"]
          );
          products
            .then((products_list) => {
              $("#ModalTitle").html("Add Products To MRP Plan");
              $("#tableBody").html("");
              $("#tableHead").html("");
              $("#bodyTitle").html("");
              $("#newRow").html("");
              this.hideElement("dynamic-input-form", false);
              $("#addRow")
                .off("click")
                .on(
                  "click",
                  function () {
                    var row = this.addFormRow(row_id);
                    row_id = row_id + 1;
                    document.getElementById("newRow").prepend(row);
                    var selectProduct =
                      document.getElementById("select-product-id");
                    products_list.forEach(
                      function (optionValue) {
                        var option = this.addSelectOption(
                          optionValue["display_name"],
                          optionValue["id"]
                        );
                        selectProduct.appendChild(option);
                      }.bind(this)
                    );
                    var self = this;
                    document
                      .getElementById("select-product-id")
                      .addEventListener("change", function () {
                        var product_id = this.value;
                        var row_elemnt_parent = this.parentNode.parentNode;
                        var bom_list = self.orm.searchRead(
                          "mrp.bom",
                          [["product_id.id", "=", product_id]],
                          ["id", "display_name"]
                        );
                        var selectBom =
                          row_elemnt_parent.querySelector("#product-bom-id");
                        bom_list.then((bom_list) => {
                          selectBom.innerHTML = "";
                          bom_list.forEach(function (optionValue) {
                            var option = self.addSelectOption(
                              optionValue["display_name"],
                              optionValue["id"]
                            );
                            selectBom.appendChild(option);
                          });
                          var df_option = self.addSelectOption("Empty", "");
                          selectBom.appendChild(df_option);
                        });
                      });
                  }.bind(this)
                );
              document
                .getElementById("newRow")
                .addEventListener("click", function (e) {
                  if (e.target.classList.contains("removeRow")) {
                    e.target.closest(".row").remove();
                  }
                });
              $("#save")
                .off("click")
                .on(
                  "click",
                  function () {
                    var formData = [];
                    var inputFields =
                      document.querySelectorAll('[name="name[]"]');
                    inputFields.forEach(function (input) {
                      formData.push(input.value);
                    });
                    for (var i = 0; i < formData.length; i += 3) {
                      var prod_id = formData[i];
                      var bom_id = formData[i + 1];
                      var sst = formData[i + 2];
                      var new_mrp_pla_lines = this.createMrpPlanLines(
                        prod_id,
                        bom_id,
                        sst,
                        mrp_plan_id
                      );
                      new_mrp_pla_lines
                        .then((result) => {
                          var mrp_plan_lines_notif =
                            this.notificationService.add(
                              "The Product " +
                                result[0] +
                                " Successfully Created",
                              {
                                title: "Add Product To MRP Plan",
                                type: "success",
                              }
                            );
                          setTimeout(mrp_plan_lines_notif, 2000);
                          $("#PDPValidationModel").modal("hide");
                          setTimeout(function () {
                            location.reload(true);
                          }, 2000);
                        })
                        .catch((error) => {
                          var mrp_plan_lines_notif =
                            this.notificationService.add(
                              "Err, Product must be unique within the same Plan, Please contact your system administrator",
                              {
                                title: "Add Product To MRP Plan",
                                type: "danger",
                              }
                            );
                          setTimeout(mrp_plan_lines_notif, 2000);
                          $("#PDPValidationModel").modal("hide");
                        });
                    }
                  }.bind(this)
                );
              $("#PDPValidationModel").modal("show");
            })
            .catch((error) => {});
        }.bind(this)
      );

      monthly_tab.on(
        "headerDblClick",
        function (e, column) {
          $("#tableBody").html("");
          $("#tableHead").html("");
          if (column.getField() !== "Product") {
            var date = new Date(column.getField());
            var prod = [];
            var start_date = this.formatDate(column.getField(), -1);
            var end_date = this.getLastDayOfMonth(start_date);
            monthly_tab.getData().forEach(function (row) {
              prod.push(row["Product"]);
            });
            var prod_ids = this.getValueBasedOnKey(
              prod,
              this.state.mrp_plan_product_data,
              "product",
              "productID"
            );
            var weekly_data = this.getWeeklyPlan(
              prod_ids,
              start_date,
              end_date
            ); // check end date return wrong day (29 intead of 31 for dec)
            weekly_data
              .then((result) => {
                var [main_weekly_data, tab_data] = this.data_nest(
                  result,
                  "weekly"
                );
                this.state.weekly_mrp_plan_product_data = main_weekly_data;
                let modal = document.getElementById("WeeklyPlaModel");
                this.addTabtToModal();
                var weekly_columns = this.getTabCols(tab_data, "weekly");
                weekly_tab = this.setupTabulator(
                  tab_data,
                  weekly_columns,
                  "#WeeklyTab"
                );
              })
              .catch((error) => {
                console.error(error); // Handle any errors
              });
            $("#WeeklyPlaModel").modal("show");
          }
        }.bind(this)
      );
    });
  }

  addTabtToModal() {
    // Create a div element with class and id
    let tab = document.createElement("div");
    tab.className = "table table-hover"; // Add class
    tab.id = "WeeklyTab"; // Add id
    let modalBody = document.getElementById("WeeklyPlanmodalBody");
    modalBody.appendChild(tab);
  }

  updateObjectById(proxyArray, id, key, value) {
    return proxyArray.map((obj) => {
      if (obj.id === id) {
        return { ...obj, [key]: value };
      } else {
        return obj;
      }
    });
  }

  async getWeeklyPlan(prod_list_ids, start_date, end_date) {
    var data = this.orm.searchRead(
      "product.mrp.plan.weekly",
      [
        ["product_id.id", "in", prod_list_ids],
        ["date", ">=", start_date],
        ["date", "<=", end_date],
      ],
      [
        "quantity",
        "date",
        "product_id",
        "expected_start_quantity",
        "sale_planned_quantity",
        "lot_size",
        "expected_final_quantity",
        "sale_capacity",
        "autonomy",
        "pdp_validation",
      ]
    );
    var res = [];
    await data
      .then((result) => {
        res = result;
      })
      .catch((error) => {
        console.error(error);
      });
    return res;
  }

  getTabCols(data, type = "monthly") {
    if (data.length > 0) {
      var cols = Object.keys(data[0]);
      var columns = Object.keys(data[0]).map((key) => {
        if (type == "monthly") {
          if (key === "Product") {
            return {
              title: key,
              field: key,
              headerFilter: true,
              formatterParams: { type: "monthly" },
              formatter: this.actionButtonFormatter.bind(this),
              headerFilterPlaceholder: "Find a Product...",
              widthGrow: 2,
            };
          } else {
            return {
              title: key,
              field: key,
              editor: "number",
              formatterParams: { type: "monthly" },
              formatter: this.actionFormatterSplitCell.bind(this),
              cellEdited: this.monthlycellEdited.bind(this),
            };
          }
        } else {
          if (key === "Product") {
            return {
              title: key,
              field: key,
              headerFilter: true,
              formatterParams: { type: "weekly" },
              formatter: this.actionButtonFormatter.bind(this),
              headerFilterPlaceholder: "Find a Product...",
            };
          } else {
            return {
              title: key,
              field: key,
              editor: "number",
              formatterParams: { type: "weekly" },
              formatter: this.actionFormatterSplitCell.bind(this),
              cellEdited: this.weeklyCellEdited.bind(this),
            };
          }
        }
      });
      return columns;
    } else {
      return [];
    }
  }

  actionFormatterSplitCell(cell, formatterParams, onRendered) {
    var cellElement = cell.getElement();
    // Create the split cell container
    var container = document.createElement("div");
    container.classList.add("split-cell");
    // Create the cell value container
    var valueContainer = document.createElement("div");
    valueContainer.classList.add("cell-content");
    valueContainer.textContent = cell.getValue();
    // Create the button container
    var buttonContainer = document.createElement("div");
    buttonContainer.classList.add("button-container");
    // Create the button element
    var button = document.createElement("button");
    button.classList.add("badge");
    button.classList.add("btn-outline-secondary");
    // button.classList.add('rounded-pill');
    button.classList.add("road-map-qty");

    container.appendChild(valueContainer);
    buttonContainer.appendChild(button);
    container.appendChild(buttonContainer);
    var product = cell.getTable().getData()[0]["Product"];
    if (formatterParams["type"] === "monthly") {
      var date = this.formatDate(cell.getColumn().getField(), -1);
      var prod_id = this.searchItem(
        this.state.monthly_data,
        "date",
        date,
        "product",
        product,
        "productID"
      );
    } else {
      var date = cell.getColumn().getField();
      var prod_id = this.searchItem(
        this.state.weekly_mrp_plan_product_data,
        "date",
        date,
        "product",
        product,
        "productID"
      );
    }
    var roadMap = this.getRoadMapData(prod_id, date);
    var recordId = -1;
    roadMap
      .then((result) => {
        // console.log('getRoadMapData',result)
        if (result.length > 0) {
          button.textContent = result[0]["quantity"];
          recordId = result[0]["id"];
        } else {
          button.textContent = 0;
        }
      })
      .catch((error) => {
        console.log("ERR: ", error);
      });

    button.addEventListener(
      "click",
      function (e) {
        if (e.target) {
          e.stopPropagation();
          if (recordId != -1) {
            this.env.services.action.doAction({
              type: "ir.actions.act_window",
              res_model: "mrp.roadmap",
              res_id: recordId,
              views: [[false, "form"]],
              target: "current",
            });
          }
        }
      }.bind(this)
    );
    return container;
  }

  actionButtonFormatter(cell, formatterParams, onRendered) {
    // Create the split cell container
    var container = document.createElement("div");
    container.classList.add("split-cell");
    // Create the cell value container
    var valueContainer = document.createElement("div");
    valueContainer.classList.add("cell-value");
    valueContainer.textContent = cell.getValue();
    // Create the button container
    var buttonContainer = document.createElement("div");
    buttonContainer.classList.add("button-container");
    // Create the button element
    var button = document.createElement("button");
    button.id = "detailsButton";
    var img = document.createElement("img");
    img.src = "dw_mrp_plan/static/src/components/tab/list.svg";
    img.alt = "Icon";
    button.appendChild(img);
    button.addEventListener(
      "click",
      function (e) {
        e.stopPropagation(); // Prevent cell click event from triggering
        var cellValue = cell.getValue();
        if (formatterParams["type"] === "monthly") {
          var proxy_details = this.state.mrp_plan_product_data.filter(
            (obj) => obj["product"] === cellValue
          );
        } else {
          var proxy_details = this.state.weekly_mrp_plan_product_data.filter(
            (obj) => obj["product"] === cellValue
          );
        }
        $("#tableBody").html("");
        $("#tableHead").html("");
        this.addTableHead();
        const list_details = proxy_details.map((proxyObject) => {
          const newObj = {};
          for (let key of Object.keys(proxyObject)) {
            newObj[key] = proxyObject[key];
          }
          this.addTableRow(
            newObj["id"],
            this.formatDate(newObj["date"]),
            newObj["expected_final_quantity"],
            newObj["expected_start_quantity"],
            newObj["lot_size"],
            newObj["quantity"],
            newObj["sale_capacity"],
            newObj["sale_planned_quantity"],
            newObj["pdp_validation"]
          );
          return newObj;
        });
        if (formatterParams["type"] === "monthly") {
          $("#bodyTitle").text(list_details[0]["product"]);
        } else {
          $("#bodyTitle").text(
            list_details[0]["product"] +
              "/ Weekly Plan For: " +
              this.formatDate(list_details[0]["date"])
          );
        }

        $("#ModalTitle").text("Product MRP Plan Validation");
        this.hideElement("dynamic-input-form");
        $("#PDPValidationModel").modal("show");
        document
          .getElementById("checkAll")
          .addEventListener("change", function () {
            var checkboxes = document.querySelectorAll(".checkBox");
            checkboxes.forEach(
              function (checkbox) {
                if (!checkbox.disabled) {
                  checkbox.checked = this.checked;
                }
              }.bind(this)
            );
          });
        $("#save")
          .off("click")
          .on(
            "click",
            function () {
              var checkboxes = document.querySelectorAll(".checkBox");
              var checkedValues = [];
              checkboxes.forEach(
                function (checkbox) {
                  if (checkbox.checked && !checkbox.disabled) {
                    checkedValues.push(checkbox.value);
                  }
                }.bind(this)
              );
              var close = this.notificationService.add(
                "All Selected Records Has Been Updated Successfully",
                {
                  title: "Success",
                  type: "success",
                }
              );
              setTimeout(close, 2000);
              this.validateDates(checkedValues, formatterParams["type"]);
              $("#PDPValidationModel").modal("hide");
            }.bind(this)
          );
      }.bind(this)
    );
    // Append the value and button containers to the split cell container
    container.appendChild(valueContainer);
    buttonContainer.appendChild(button);
    container.appendChild(buttonContainer);
    return container;
  }

  async getMrpPlanList() {
    var data = this.orm.searchRead(
      "mrp.plan",
      [[1, "=", 1]],
      ["name", "season_date", "id"]
    );
    var res = [];
    await data
      .then((result) => {
        res = result;
      })
      .catch((error) => {
        console.error(error);
      });
    return res;
  }

  validateDates(ids_list, type) {
    ids_list.forEach((id, step) => {
      (function (recordId, step) {
        setTimeout(
          function () {
            if (type == "monthly") {
              this.orm.write("product.mrp.plan", [parseInt(id)], {
                ["pdp_validation"]: true,
              });
              this.state.mrp_plan_product_data = this.updateObjectById(
                this.state.mrp_plan_product_data,
                parseInt(id),
                "pdp_validation",
                true
              );
            } else {
              this.orm.write("product.mrp.plan.weekly", [parseInt(id)], {
                ["pdp_validation"]: true,
              });
              this.state.weekly_mrp_plan_product_data = this.updateObjectById(
                this.state.weekly_mrp_plan_product_data,
                parseInt(id),
                "pdp_validation",
                true
              );
            }
          }.bind(this),
          100 * step
        );
      }).bind(this)(id, step);
    });
  }

  addTableRow(
    id,
    Date,
    expected_final_quantit,
    expected_start_quantity,
    lot_size,
    quantity,
    sale_capacity,
    sale_planned_quantity,
    pdp_validation
  ) {
    var newRow = $("<tr>");
    var checked = "";
    if (pdp_validation == true) {
      checked = "checked disabled";
      newRow.addClass("pdp_row_highlight");
    }
    newRow.append(
      '<td> <input type="checkbox" value = "' +
        id +
        '" class="checkBox" ' +
        checked +
        "/> </td>"
    );
    newRow.append("<td>" + Date + "</td>");
    newRow.append("<td>" + expected_final_quantit + "</td>");
    newRow.append("<td>" + expected_start_quantity + "</td>");
    newRow.append("<td>" + lot_size + "</td>");
    newRow.append(
      '<td> <span class="badge rounded-pill bg-primary" style="font-size: 16px;"> ' +
        quantity +
        "</span> </td>"
    );
    newRow.append("<td>" + sale_capacity + "</td>");
    newRow.append("<td>" + sale_planned_quantity + "</td>");
    $("#tableBody").append(newRow);
  }

  addTableHead() {
    var head = $("<tr>");
    head.append('<th scope="col"><input type="checkbox" id="checkAll"/></th>');
    head.append('<th scope="col">Date</th>');
    head.append('<th scope="col">Expected Final Quantit</th>');
    head.append('<th scope="col">Expected Start Quantity</th>');
    head.append('<th scope="col">Lot Size</th>');
    head.append('<th scope="col">Quantity</th>');
    head.append('<th scope="col">Sale Capacity</th>');
    head.append('<th scope="col">Sale Planned Quantity</th>');
    $("#tableHead").append(head);
  }

  addProductsTableHead() {
    var head = $("<tr>");
    head.append('<th scope="col"><input type="checkbox" id="checkAll"/></th>');
    head.append('<th scope="col">Product</th>');
    head.append('<th scope="col">BOM</th>');
    head.append('<th scope="col">Safety Stock Target</th>');
    $("#tableHead").append(head);
  }

  addFormRow(prod_id = "id") {
    var row = document.createElement("div");
    row.className = "row mt-3";
    row.innerHTML = `
             <div class="col-md-3 form-floating">
                <select class="form-select" name="name[]" id="select-product-id">
                </select>
                <label for="select-product-id">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Select Product</label>
            </div>

            <div class="col-md-3 form-floating">
                <select class="form-select" name="name[]" id="product-bom-id">
                    <option value="">Empty</option>
                </select>
                <label for="product-bom-id">&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;Select BOM</label>

            </div>

            <div class="col-md-3">
                <input type="number" value=0 name="name[]" id="product-sst-id" class="form-control" placeholder="Safety Stock Target">
            </div>

            <div class="col-md-3">
                <button class="btn btn-danger removeRow">Remove</button>
            </div>
        `;
    return row;
  }

  formatDate(dateString, type = 1) {
    if (type == 1) {
      const date = new Date(dateString);
      const options = { year: "numeric", month: "short" };
      return date.toLocaleDateString("en-US", options);
    } else {
      var parts = dateString.split(" ");
      var month = parts[0];
      var year = parseInt(parts[1]);
      var monthNumber = new Date(Date.parse(month + " 1, 2020")).getMonth() + 1;
      var formattedDate = year + "-" + ("0" + monthNumber).slice(-2) + "-01";
      return formattedDate;
    }
  }

  getLastDayOfMonth(dateString) {
    // Parse the date string
    let parts = dateString.split("-");
    let year = parseInt(parts[0]);
    let month = parseInt(parts[1]) - 1; // Adjust month to zero-based index
    let day = parseInt(parts[2]);
    let date = new Date(year, month, day);
    date.setDate(0);
    date.setMonth(date.getMonth() + 1);
    let lastDayOfMonth = date.toISOString().slice(0, 10);
    return lastDayOfMonth;
  }

  setupTabulator(data, columns, id) {
    var table = new Tabulator(id, {
      height: "auto",
      layout: "fitColumns",
      data: data,
      pagination: "local",
      paginationSize: 6,
      paginationSizeSelector: [3, 5, 8, 12, 20, 30],
      movableColumns: true,
      paginationCounter: "rows",
      columns: columns,
    });
    return table;
  }

  searchItem(proxyList, key1, value1, key2, value2, returnField) {
    for (let item of proxyList) {
      if (item[key1] === value1 && item[key2] === value2) {
        return item[returnField];
      }
    }
    return null;
  }

  getValueBasedOnKey(prod_list, proxyList, otherKey, targetKey) {
    var ids = [];
    for (let prod of prod_list) {
      var proxy = proxyList.find(function (item) {
        return item[otherKey] === prod;
      });
      if (proxy) {
        ids.push(proxy[targetKey]);
      }
    }
    return ids;
  }

  customEditor(cell, onRendered, success, cancel) {
    console.log("=== inside etidor -----");
    // Create and style input element
    var input = document.createElement("input");
    input.setAttribute("type", "text");
    input.style.width = "100%";
    input.style.boxSizing = "border-box";

    // Set initial value
    input.value = cell.getValue();

    // Focus on input element when editor is rendered
    onRendered(function () {
      input.focus();
      input.style.height = "100%";
    });

    // When user presses enter, update cell value and close editor
    input.addEventListener("blur", function (e) {
      success(input.value);
    });

    // Add input to cell
    cell.getElement().appendChild(input);
    return input;
  }

  async monthlycellEdited(cell) {
    const editedValue = cell.getValue();
    const columnField = cell.getField();
    const prod = cell.getData()["Product"];
    var pdp_validated = this.searchItem(
      this.state.mrp_plan_product_data,
      "date",
      this.formatDate(columnField, -1),
      "product",
      prod,
      "pdp_validation"
    );
    if (pdp_validated === true) {
      cell.getElement().style.backgroundColor = "#ADD8E6";
      cell.restoreOldValue();
    } else {
      var record_id_to_update = this.searchItem(
        this.state.mrp_plan_product_data,
        "date",
        this.formatDate(columnField, -1),
        "product",
        prod,
        "id"
      );
      cell.getElement().setAttribute("contenteditable", false);
      try {
        var prod_name = cell.getData()["Product"];
        await this.orm.write("product.mrp.plan", [record_id_to_update], {
          ["quantity"]: editedValue,
        });
        console.log("Field value updated successfully");
        this.state.mrp_plan_product_data = this.updateObjectById(
          this.state.mrp_plan_product_data,
          record_id_to_update,
          "quantity",
          editedValue
        );
      } catch (error) {
        console.error("Catching Error updating field value:", error);
      }
    }
  }

  async weeklyCellEdited(cell) {
    const editedValue = cell.getValue();
    const columnField = cell.getField();
    const prod = cell.getData()["Product"];
    var pdp_validated = this.searchItem(
      this.state.weekly_mrp_plan_product_data,
      "date",
      columnField,
      "product",
      prod,
      "pdp_validation"
    );
    if (pdp_validated === true) {
      cell.getElement().style.backgroundColor = "#ADD8E6";
      cell.restoreOldValue();
    } else {
      var record_id_to_update = this.searchItem(
        this.state.weekly_mrp_plan_product_data,
        "date",
        columnField,
        "product",
        prod,
        "id"
      );
      try {
        var prod_name = cell.getData()["Product"];
        await this.orm.write("product.mrp.plan.weekly", [record_id_to_update], {
          ["quantity"]: editedValue,
        });
        this.state.weekly_mrp_plan_product_data = this.updateObjectById(
          this.state.weekly_mrp_plan_product_data,
          record_id_to_update,
          "quantity",
          editedValue
        );
        console.log("Field value updated successfully");
      } catch (error) {
        console.error("Error updating field value:", error);
      }
    }
  }

  async get_mrp_plan_product_data(year, id = false) {
    if (id) {
      var data = this.orm.searchRead(
        "product.mrp.plan",
        [
          [1, "=", 1],
          ["product_plan_id.plan_id.id", "=", id],
        ],
        [
          "quantity",
          "date",
          "product_id",
          "expected_start_quantity",
          "sale_planned_quantity",
          "lot_size",
          "expected_final_quantity",
          "sale_capacity",
          "autonomy",
          "pdp_validation",
        ]
      );
    } else {
      var data = this.orm.searchRead(
        "product.mrp.plan",
        [
          [1, "=", 1],
          ["product_plan_id.plan_id.season_date", "=", year],
        ],
        [
          "product_plan_id",
          "quantity",
          "date",
          "product_id",
          "expected_start_quantity",
          "sale_planned_quantity",
          "lot_size",
          "expected_final_quantity",
          "sale_capacity",
          "autonomy",
          "pdp_validation",
        ]
      );
    }
    var res = [];
    await data
      .then((result) => {
        res = result;
      })
      .catch((error) => {
        console.error(error);
      });
    return res;
  }

  data_nest(data, type) {
    if (data.length === 0) {
      return [[], []];
    } else {
      data.forEach((dict) => {
        for (const key in dict) {
          dict["product"] = dict["product_id"][1];
          dict["productID"] = dict["product_id"][0];
        }
      });
      const groupedData = d3
        .nest()
        .key((d) => d["product"]) // Group by product
        .entries(data);
      var res = [];
      var r = {};
      groupedData.forEach((row) => {
        r["Product"] = row.key;
        row.values.forEach((row1) => {
          if (type == "monthly") {
            r[this.formatDate(row1["date"])] = row1["quantity"];
          } else {
            r[row1["date"]] = row1["quantity"];
          }
        });
        res.push(r);
        r = {};
      });
      return [data, res];
    }
  }

  addSelectOption(text, value) {
    var option = document.createElement("option");
    option.text = text;
    option.value = value; // Set both text and value to the same value
    return option;
  }

  async getSalePlanData(company_id) {
    var data = this.orm.searchRead(
      "sale.plan",
      ["|", ["company_id.id", "=", company_id], ["company_id", "=", false]],
      ["id", "name"]
    );
    var res = [];
    await data
      .then((result) => {
        res = result;
      })
      .catch((error) => {
        console.error(error);
      });
    return res;
  }

  async getCompanyData() {
    var data = this.orm.searchRead(
      "res.company",
      [[1, "=", 1]],
      ["id", "name"]
    );
    var res = [];
    await data
      .then((result) => {
        res = result;
      })
      .catch((error) => {
        console.error(error);
      });
    return res;
  }

  createMrpPlan(plan_name, plan_season, plan_company_id, plan_sale_plan_id) {
    var new_mrp_plan = this.orm.create("mrp.plan", [
      {
        name: plan_name,
        season_date: plan_season,
        sale_plan_id: plan_sale_plan_id,
        company_id: plan_company_id,
      },
    ]);
    return new_mrp_plan;
  }

  createMrpPlanLines(prod_id, bom_id, sst, plan_id) {
    var new_mrp_plan_lines = this.orm.create("mrp.plan.lines", [
      {
        product_id: parseInt(prod_id),
        bom_id: parseInt(bom_id),
        safety_stock_target: sst,
        plan_id: parseInt(plan_id),
      },
    ]);
    return new_mrp_plan_lines;
  }

  hideElement(id, hide = true) {
    var div = document.getElementById(id);
    if (div) {
      if (hide) {
        div.style.display = "none";
      } else {
        div.style.display = "block";
      }
    }
  }

  async getRoadMapData(product, date) {
    return await this.orm.searchRead(
      "mrp.roadmap",
      [
        ["product_id.id", "=", product],
        ["date", "=", date],
      ],
      []
    );
  }

  btnCreateMrpPla() {
    var company_data = this.getCompanyData();
    company_data
      .then((result) => {
        var selectCompanyMrpPlan = document.getElementById(
          "select-mrp-plan-company"
        );
        selectCompanyMrpPlan.innerHTML = "";
        result.forEach(
          function (optionValue) {
            var option = this.addSelectOption(
              optionValue["name"],
              optionValue["id"]
            );
            selectCompanyMrpPlan.appendChild(option);
          }.bind(this)
        );
        var company_id = $("#select-mrp-plan-company").val();
        var sale_plan_data = this.getSalePlanData(company_id);
        sale_plan_data
          .then((result) => {
            var select_sale_plan = document.getElementById(
              "select-mrp-sale-plan"
            );
            select_sale_plan.innerHTML = "";
            result.forEach(
              function (optionValue) {
                var option = this.addSelectOption(
                  optionValue["name"],
                  optionValue["id"]
                );
                select_sale_plan.appendChild(option);
              }.bind(this)
            );
            var df_option = this.addSelectOption("Empty", "");
            select_sale_plan.appendChild(df_option);
          })
          .catch((error) => {
            console.error(error); // Handle any errors
          });
      })
      .catch((error) => {
        console.error(error); // Handle any errors
      });
    $("#select-mrp-plan").val("Select Option ...");
    $("#createMrpPlanModel").modal("show");
  }
}
OwlMainDashboard.template = "owl.OwlMainDashboard";
registry.category("actions").add("owl.main_dashboard", OwlMainDashboard);
