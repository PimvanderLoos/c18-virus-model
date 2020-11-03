var ResettableCanvasModule = function(canvas_width, canvas_height, grid_width, grid_height) {
    // Create the element
    // ------------------

    // Create the tag with absolute positioning :
    var canvas_tag = `<canvas width="${canvas_width}" height="${canvas_height}" class="world-grid"/>`

    var parent_div_tag = '<div id="world-grid-canvas-block" style="height:' + canvas_height + 'px;" class="world-grid-parent"></div>'

    // Append it to body:
    var canvas = $(canvas_tag)[0];
    var interaction_canvas = $(canvas_tag)[0];
    var parent = $(parent_div_tag)[0];

    //$("body").append(canvas);
    $("#elements").append(parent);
    parent.append(canvas);
    parent.append(interaction_canvas);

    // Create the context for the agents and interactions and the drawing controller:
    var context = canvas.getContext("2d");

    width = canvas_width;
    height = canvas_height;

    previousNode = document.getElementById("world-grid-canvas-block").previousSibling;

    // Create an interaction handler using the
    var interactionHandler = new InteractionHandler(canvas_width, canvas_height, grid_width, grid_height, interaction_canvas.getContext("2d"));
    var canvasDraw = new GridVisualization(canvas_width, canvas_height, grid_width, grid_height, context, interactionHandler);

    this.render = function(data) {
        verifyCurrentDims();
        canvasDraw.resetCanvas();
        for (var layer in data)
            canvasDraw.drawLayer(data[layer]);
        canvasDraw.drawGridLines("#eee");
    };

    this.reset = function() {
        canvasDraw.resetCanvas();
    };

    function verifyCurrentDims() {
        let grid_data_url = location.href.split("#")[0] + "grid_data";

        var request = makeHttpObject();
        request.open("GET", grid_data_url, true);
        request.send(null);
        request.onreadystatechange = function() {
            if (request.readyState === 4)
                parseGridData(request.responseText);
        };
    }

    function makeHttpObject() {
        try {return new XMLHttpRequest();}
        catch (error) {}
        try {return new ActiveXObject("Msxml2.XMLHTTP");}
        catch (error) {}
        try {return new ActiveXObject("Microsoft.XMLHTTP");}
        catch (error) {}

        throw new Error("Could not create HTTP request object.");
    }

    function parseGridData(data) {
        let dims = data.split(" ");
        let new_width = parseInt(dims[0]);
        let new_height = parseInt(dims[1]);
        if (width !== new_width || height !== new_height) {
            updateDims(new_width, new_height);
        }
    }

    function updateDims(new_width, new_height) {
        interactionHandler = new InteractionHandler(new_width, new_height, grid_width, grid_height, interaction_canvas.getContext("2d"));
        canvasDraw = new GridVisualization(new_width, new_height, grid_width, grid_height, context, interactionHandler);

        var oldElement = document.getElementById("world-grid-canvas-block");

        oldElement.style.width = new_width;
        oldElement.style.height = new_height;
        location.reload();
    }
};
