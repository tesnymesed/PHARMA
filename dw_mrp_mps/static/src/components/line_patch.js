/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MpsLineComponent from '@mrp_mps/components/line';

//
//testPatch() {
//        console.log("THIS is a test patch from <<</home/bislem/SI/src/DW_PHARMA/dw_mrp_mps/static/src/components/line.js >>>");
//};


patch(MpsLineComponent.prototype, {
  setup() {
        console.log("THIS is a test patch from <<</home/bislem/SI/src/DW_PHARMA/dw_mrp_mps/static/src/components/line.js >>>");
        return super.setup();
  },
});
