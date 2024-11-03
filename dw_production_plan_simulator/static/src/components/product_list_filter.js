/** @odoo-module **/

import {
  Component,
  useState,
  onMounted,
  onPatched,
  onWillStart,
  useEnv,
  useSubEnv,
} from "@odoo/owl";

class NestedProductList extends Component {
  setup() {
    this.model = this.env.model;

    this.state = useState({
      allChecked: true,
    });

    this.model.selectAll();

    // onWillStart(() => {
    //   console.log(
    //     "🚀 ~ NestedProductList ~ onWillStart ~ onWillStart:",
    //     onWillStart
    //   );
    //   // this.model.selectAll();
    //   // this.toggleAll();
    // });

    onMounted(() => {
      this.env?.parent?.component?.setupEventHandlers();
      // this.model.selectAll();
      // this.toggleAll();
    });

    onPatched(() => {
      if (this.model.isSelected("ALL") && !this.allChecked) {
        this.model.selectAll();
      }
    });
  }

  get workCenters() {
    return this.model.workCenters;
  }

  get allChecked() {
    return this.workCenters.every((workCenter) =>
      this.model.isSelected(workCenter.key)
    );
  }

  // Update UI when selection changes
  updateState(selectedIds) {
    this.render(true); // Re-render the component to reflect selection state
  }

  toggleAll() {
    this.model._toggleAll();
  }

  // toggleAll() {
  //   this.model.toggleSelection();
  // }

  toggleWorkCenter(workCenterKey) {
    const workCenterSelected = this.model.isSelected(workCenterKey);
    const workCenter = this.workCenters.find((wc) => wc.key === workCenterKey);

    if (workCenterSelected) {
      // Deselect the work center and all its products
      this.model.deselectRecord(workCenterKey);
      workCenter.values.forEach((product) =>
        this.model.deselectRecord(product.id)
      );
    } else {
      // Select the work center and all its products
      this.model.selectRecord(workCenterKey);
      workCenter.values.forEach((product) =>
        this.model.selectRecord(product.id)
      );
    }

    // Update the "ALL" checkbox based on the new selection state
    this.updateAllCheckbox();
  }

  // Toggle a product and propagate the change to the workCenter
  toggleProduct(workCenterKey, productId) {
    this.model.toggleRecordSelection(productId);

    const workCenter = this.workCenters.find((wc) => wc.key === workCenterKey);
    const allProductsSelected = workCenter.values.every((product) =>
      this.model.isSelected(product.id)
    );
    if (allProductsSelected) {
      this.model.selectRecord(workCenterKey);
    } else {
      this.model.deselectRecord(workCenterKey);
    }
    this.updateAllCheckbox();
  }

  updateAllCheckedState() {
    this.state.allChecked = this.workCenters.every(
      (workCenter) => this.model.isSelected(workCenter.key)
      // &&
      //   workCenter.values.every((p) => this.model.isSelected(p.is))
    );
  }

  updateAllCheckbox() {
    if (this.allChecked) {
      this.model.selectRecord("ALL");
    } else {
      this.model.deselectRecord("ALL");
    }
  }
}

NestedProductList.template =
  "production_plan_simulator.NestedProductListTemplate";

export default NestedProductList;
