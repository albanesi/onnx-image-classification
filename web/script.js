function checkFiles(files) {
    if (files.length != 1) {
        alert("Bitte genau eine Datei hochladen.");
        return;
    }

    const fileSize = files[0].size / 1024 / 1024;
    if (fileSize > 10) {
        alert("Datei zu gross (max. 10MB)");
        return;
    }

    answerPart.style.visibility = "visible";
    const file = files[0];

    // Vorschau
    if (file) {
        preview.src = URL.createObjectURL(files[0]);
    }

    const formData = new FormData();
    formData.append("0", file);

    fetch('/analyze', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
    .then(data => {
        console.log(data);

        let allTables = "<div class='row'>";
        for (const model in data) {
            let table = `
                <div class='col-md-6'>
                    <h5>${model}</h5>
                    <table class='table table-bordered table-striped'>
                        <thead><tr><th>Class</th><th>Confidence</th></tr></thead><tbody>`;
            data[model].forEach(item => {
                table += `<tr><td>${item.class}</td><td>${(item.value * 100).toFixed(2)}%</td></tr>`;
            });
            table += "</tbody></table></div>";
            allTables += table;
        }
        allTables += "</div>";
        answer.innerHTML = allTables;
    })
    .catch(error => {
        console.error(error);
        answer.innerHTML = "<p style='color:red;'>Fehler beim Analysieren des Bildes.</p>";
    });
}
