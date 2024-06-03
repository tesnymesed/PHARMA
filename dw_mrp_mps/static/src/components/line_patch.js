
/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import MpsLineComponent from '@mrp_mps/components/line';
import { Component, useExternalListener, useState, onMounted, onWillStart, useRef, useEffect } from "@odoo/owl";

patch(MpsLineComponent.prototype, {
    setup() {
        let data = this.props.data;
        let forecastIds = data.forecast_ids;


        super.setup();

        onMounted(() => {
            this.index = this.findCurrentPeriodIdx(forecastIds)
            this.disableHeaderCells();
            this.disableTableContentCells();

        });

    },

    disableHeaderCells() {
        var header = document.getElementsByClassName('o_mps_period');
        if (header.length > 0) {
            header = header[0];
        }

        var nestedElements = header.getElementsByTagName('th');

        for (var i = 3; i < 3 + this.index; i++) {
            this.disableElement(nestedElements[i]);
        };
    },

    disableTableContentCells() {
        var elements = document.getElementsByClassName('o_mps_content'); // tbody
        for (var j = 0; j < elements.length; j++) {
            var trNestedElements = elements[j].getElementsByTagName('tr');

            for (var k = 0; k < trNestedElements.length; k++) {
                var thNestedElements = trNestedElements[k].getElementsByTagName('th');

                for (var i = 3; i < 3 + this.index; i++) {
                    this.disableElement(thNestedElements[i]);
                }

            }
        }


    },

    disableElement(elt) {
        elt.setAttribute('disabled', 'disabled');
        elt.style.pointerEvents = 'none';
        elt.style.opacity = '0.5';
    },

    findCurrentPeriodIdx(periods) {
        var today = new Date();
        today.setHours(0, 0, 0, 0); // Set time to midnight for comparison


        var index = periods.findIndex(function (p) {
            var startDate = new Date(p.date_start);
            var endDate = new Date(p.date_stop);
            return (startDate <= today && endDate >= today)
        });

        return index;

    }

});
