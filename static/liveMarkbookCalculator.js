let initialMarks = {};

/**
 * @desc Takes in a mark layer and calculates the total mark based off weights and raw score
 * @param {Array} layer Mark layer to be calculated
 * @returns {Number} Overall mark of the current layer
 */
const calculateLayer = layer => {
    let sum = 0;
    let denominator = 0;
    for (let i = 0; i < layer.length; i++) {
        let mark = parseFloat(layer[i].mark);
        let weight = parseFloat(layer[i].weight);
        let markDenom = parseFloat(layer[i].denominator);

        if (isNaN(mark) || isNaN(weight) || isNaN(markDenom)) // EXC, ABS, and blanks are ignored
            continue;

        if (mark < 0) // Treat negative marks as 0
            mark = 0;
        if (weight < 0) // Treat negative weights as 0
            weight = 0;
        if (markDenom <= 0) // If the denominator does not make sense, ignore whole grade
            continue;
        denominator += weight;
        sum += (mark / markDenom) * weight;

        /* Update the mark display */
        let row = layer[i].row;
        if (row) {
            row.find('td:nth-child(2) > input').val(+mark.toFixed(2));
            row.find('td:nth-child(4) > input').val(weight);
            row.find('td:nth-child(5) > input').val(markDenom);
        }
    }

    return parseFloat(sum / denominator); // Return the new mark as a decimal
};

/**
 * @desc Runs the whole markbook through the layer calculator and modifies the displayed markbook
 */
const calculateMarks = () => {
    let markbook = parseMarkbook();

    for (let i = 0; i < markbook.length; i++) {
        let middle = markbook[i].children;

        if ((isNaN(parseFloat(markbook[i].mark)) && markbook[i].mark !== '') || markbook[i].row.find('td:nth-child(2) > input').is(':hidden')) // Make sure top isn't already invalid or hidden
            continue;

        if (middle && middle.length) { // Make sure there is a middle layer to handle
            for (let j = 0; j < middle.length; j++) {
                if ((isNaN(parseFloat(middle[j].mark)) && middle[j].mark !== '') || middle[j].row.find('td:nth-child(2) > input').is(':hidden')) // Make sure middle isn't already invalid or hidden
                    continue;

                let bottom = middle[j].children;

                if (bottom && bottom.length) { // Make sure there is a bottom layer to handle
                    markbook[i].children[j].mark = calculateLayer(bottom) * markbook[i].children[j].denominator; // Set the new mark
                }
            }

            markbook[i].mark = calculateLayer(markbook[i].children) * markbook[i].denominator; // Set the new mark
        }
    }

    let finalMark = +(calculateLayer(markbook) * 100).toFixed(3);
    let finalMarkSelector = $('#markbookTable > div > div');

    finalMarkSelector.text(`Term Mark: ${initialFinalMark} -> ${finalMark}`); // Display the final grade
    if (!isNaN(initialFinalMark) && initialFinalMark !== finalMark) {
        let difference = +parseFloat(finalMark - initialFinalMark).toFixed(3);

        if (difference > 0)
            finalMarkSelector.append(` <span style="color: #00c100;">+${difference}</span>`);
        else
            finalMarkSelector.append(` <span style="color: #c10000;">${difference}</span>`);
    }
};

/**
 * @desc Iterates over the current markbook and parses the mark information into an array
 * @returns {Array} Holds the values of the current markbook
 */
const parseMarkbook = () => {
    let markbook = [];
    $('#markbookTable table tbody > tr:gt(0)').each(function () { // Loop through each row except the first
        const row = $(this);
        const margin = row.find('td:first > span:first')[0].style['margin-left'];

        switch (margin) {
            case '0px': {
                markbook.push({
                    mark: row.find('td:nth-child(2) > input').val(),
                    weight: row.find('td:nth-child(4) > input').val(),
                    denominator: row.find('td:nth-child(5) > input').val(),
                    children: [],
                    row: row
                });
                break;
            }
            case '20px': {
                markbook[markbook.length - 1].children.push({ // Push a middle row into the latest top level
                    mark: row.find('td:nth-child(2) > input').val(),
                    weight: row.find('td:nth-child(4) > input').val(),
                    denominator: row.find('td:nth-child(5) > input').val(),
                    children: [],
                    row: row
                });
                break;
            }
            case '40px': {
                let top = markbook[markbook.length - 1].children;
                let middle = !top[top.length - 1] ? top : top[top.length - 1].children;

                if (!middle) {
                    middle = top;
                }

                middle.push({
                    mark: row.find('td:nth-child(2) > input').val(),
                    weight: row.find('td:nth-child(4) > input').val(),
                    denominator: row.find('td:nth-child(5) > input').val(),
                    row: row
                });
                break;
            }
            default: {
                throw new Error('Unknown margin', margin);
            }
        }
    });
    return markbook;
};

/**
 * @desc Converts the current open markbook to an editable format
 */
const makeMarkbookEditable = () => {
    $('#markbookTable table').prepend('<style type="text/css">input[type="number"]::-webkit-outer-spin-button,input[type="number"]::-webkit-inner-spin-button {-webkit-appearance: none;margin: 0;} input[type="number"] {-moz-appearance: textfield; margin: 0; border: none; display: inline; font-family: Monaco, Courier, monospace; font-size: inherit; padding: 0; text-align: center; width: 30pt; background-color: inherit;}</style>');
    initialFinalMark = parseFloat($('#markbookTable > div > div').text().substr(11)); // Grab everything after 'Term Mark: '
    $('#markbookTable table tbody td:nth-child(n+2):nth-child(-n+5):not(:nth-child(3))').each(function () {
        const value = $(this).text();
        let inputHTML = `<input min="0" type="number" value="${value}" />`;

        if (isNaN(parseFloat(value)) && value !== '') {
            if (value === 'NHI' || value === 'INC')
                inputHTML = `<span>${value}</span><input min="0" type="number" value="0" style="display: none;" />`;
            else if (value === 'EXC' || value === 'ABS' || value === 'COL') // EXC and ABS
                inputHTML = `<span>${value}</span><input min="0" type="number" value="" style="display: none;" />`;
            else
                return; // Ignore other values
        }

        $(this).html(inputHTML);
        const input = $(this).children('input');
        const span = $(this).children('span');

        if (span) {
            $(span).bind('click', function () {
                input.show();
                calculateMarks();
                $(this).remove();
            });
        }
        $(input).bind('input', function () {
            calculateMarks();
            $(this).parent().css('background-color', '#ffe499'); // Change color of cell to indicate it was modified
        });
    });
};

const getInitialMarks = () => {
    $('.modal').each(function () {
        let modalType = $(this).attr('id').split('_')[1];
        if (modalType !== 'marks')
            return;

        const courseCode = $(this).attr('id').split('_')[0];
        const mark = parseFloat($('#' + courseCode + "_initial_mark").text()).toFixed(2);

        initialMarks[courseCode] = mark;
    });
};

const fixDecimals = () => {
    let prevVal;
    $(`input`).each(function () {
        prevVal = parseFloat($(this).val());
        $(this).val(+prevVal.toFixed(2));
    });
};
