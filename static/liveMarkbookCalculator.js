let initialMarks = {}; // Stores the initial final grade

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
            row.find('th:nth-child(3) > input:first, td:nth-child(3) > input:first').val(+mark.toFixed(2));
            row.find('th:nth-child(3) > input:last, td:nth-child(3) > input:last').val(markDenom);
            row.find('th:nth-child(4) > input, td:nth-child(4) > input').val(weight);
        }
    }

    return parseFloat(sum / denominator); // Return the new mark as a decimal
};

/**
 * @desc Runs the whole markbook through the layer calculator and modifies the displayed markbook
 */
const calculateMarks = courseCode => {
    let markbook = parseMarkbook(courseCode);

    for (let i = 0; i < markbook.length; i++) {
        let middle = markbook[i].children;

        if ((isNaN(parseFloat(markbook[i].mark)) && markbook[i].mark !== '') || markbook[i].row.find('th:nth-child(3) > input:first').is(':hidden')) // Make sure top isn't already invalid or hidden
            continue;

        if (middle && middle.length) { // Make sure there is a middle layer to handle
            for (let j = 0; j < middle.length; j++) {
                if ((isNaN(parseFloat(middle[j].mark)) && middle[j].mark !== '') || middle[j].row.find('td:nth-child(3) > input:first').is(':hidden')) // Make sure middle isn't already invalid or hidden
                    continue;

                let bottom = middle[j].children;

                if (bottom && bottom.length) { // Make sure there is a bottom layer to handle
                    markbook[i].children[j].mark = calculateLayer(bottom) * markbook[i].children[j].denominator; // Set the new mark
                }
            }

            markbook[i].mark = calculateLayer(markbook[i].children) * markbook[i].denominator; // Set the new mark
        }
    }

    let finalMark = +(calculateLayer(markbook) * 100).toFixed(2);
    let finalMarkSelector = $(`#${courseCode}_marks h5:last`);

    finalMarkSelector.text(`Mark: ${initialMarks[courseCode]}% → ${finalMark}%`); // Display the final grade
    // if (!isNaN(initialFinalMark) && initialFinalMark !== finalMark) {
    //     let difference = +parseFloat(finalMark - initialFinalMark).toFixed(2);

    //     if (difference > 0)
    //         finalMarkSelector.append(` <span style="color: #00c100;">+${difference}</span>`);
    //     else
    //         finalMarkSelector.append(` <span style="color: #c10000;">${difference}</span>`);
    // }
};

/**
 * @desc Iterates over the current markbook and parses the mark information into an array
 * @returns {Array} Holds the values of the current markbook
 */
const parseMarkbook = courseCode => {
    let markbook = [];
    $(`#${courseCode}_marks_body tr:gt(0)`).each(function () {
        const row = $(this);
        const parentClass = row.parent().attr('class');

        switch (parentClass) {
            // unit 
            case 'table-primary': {
                markbook.push({
                    mark: row.find('th:nth-child(3) > input:first').val(),
                    denominator: row.find('th:nth-child(3) > input:last').val(),
                    weight: row.find('th:nth-child(4) > input').val(),
                    children: [],
                    row: row
                });
                break;
            }
            // section
            case 'table-active': {
                markbook[markbook.length - 1].children.push({ // Push a middle row into the latest top level
                    mark: row.find('td:nth-child(3) > input:first').val(),
                    denominator: row.find('td:nth-child(3) > input:last').val(),
                    weight: row.find('td:nth-child(4) > input').val(),
                    children: [],
                    row: row
                });
                break;
            }
            // assignment
            case undefined: {
                let top = markbook[markbook.length - 1].children;
                let middle = !top[top.length - 1] ? top : top[top.length - 1].children;

                if (!middle) {
                    middle = top;
                }

                middle.push({
                    mark: row.find('td:nth-child(3) > input:first').val(),
                    denominator: row.find('td:nth-child(3) > input:last').val(),
                    weight: row.find('td:nth-child(4) > input').val(),
                    row: row
                });
                break;
            }
            default: {
                throw new Error('Unknown class', parentClass);
            }
        }
    });
    return markbook;
};

/**
 * @desc Converts the current open markbook to an editable format
 */
const makeMarkbookEditable = courseCode => {
    const markString = $(`#${courseCode}_marks h5:last`).text();
    initialMarks[courseCode] = parseFloat(markString.substr(6, markString.length - 7)); // Grab everything after 'Mark: ' and before '%'

    // bind to span
    $(`#${courseCode}_marks_body .textMarkSpan`).each(function () {
        const input = $(this).parent().children('.textMarkInput');

        const span = $(this);
        $(span).bind('click', function () {
            input.show();
            input.attr('class', 'numerator');
            calculateMarks(courseCode);
            $(this).remove(); // TODO: bind regular function to element
        });
    });
    // bind to regular inputs
    $(`#${courseCode}_marks_body .numerator, #${courseCode}_marks_body .denominator, #${courseCode}_marks_body .percentage, #${courseCode}_marks_body .weight`).each(function () { // TODO: check to make sure I want empty percentages too
        $(this).bind('input', function () {
            calculateMarks(courseCode);
            $(this).parent().css('background-color', '#ffe499'); // Change color of cell to indicate it was modified
        });
    });
};

const fixDecimals = courseCode => {
    let prevVal;
    $(`#${courseCode}_marks_body input`).each(function () {
        prevVal = parseFloat($(this).val());
        $(this).val(+prevVal.toFixed(2));
    });
};

