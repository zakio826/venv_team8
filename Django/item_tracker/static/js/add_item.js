document.addEventListener("DOMContentLoaded", function () {
    const addButton = document.getElementById("add-item");
    const itemTable = document.getElementById("item-table");
    const tbody = itemTable.querySelector("tbody");

    addButton.addEventListener("click", function () {
        // 新しい行を作成
        const newRow = document.createElement("tr");
        // 新しいth要素を作成
        const th = document.createElement("th");
        // 新しいtd要素を作成
        const td = document.createElement("td");

        // 新しいlabel要素を作成
        const label = document.createElement("label");
        label.setAttribute("for", "id_item_name");
        // アイテム名のテキスト
        const itemNumber = tbody.children.length + 1; // 行の数 + 1 を使って番号を生成
        label.textContent = "アイテム名 (" + itemNumber + "個目):";

        // フォームの各フィールドを追加
        const itemNameInput = document.createElement("input");
        itemNameInput.type = "text";
        itemNameInput.name = "item_name";
        itemNameInput.maxLength = "40";
        itemNameInput.className = "form-control";
        itemNameInput.required = true;
        itemNameInput.id = "id_item_name";
        

        const groupInput = document.createElement("input");
        groupInput.type = "hidden";
        groupInput.name = "group";
        groupInput.value = document.querySelector('input[name="group"]').value;
        groupInput.className = "form-control";
        groupInput.id = "id_group";

        const assetInput = document.createElement("input");
        assetInput.type = "hidden";
        assetInput.name = "asset";
        assetInput.value = document.querySelector('input[name="asset"]').value;
        assetInput.className = "form-control";
        assetInput.id = "id_asset";

        // thにlabel要素を追加
        th.appendChild(label);
        // 各入力フィールドを新しいtd要素に追加
        td.appendChild(itemNameInput);
        td.appendChild(groupInput);
        td.appendChild(assetInput);

        // thを新しい行に追加
        newRow.appendChild(th);
        // td要素を新しい行に追加
        newRow.appendChild(td);

        // 新しい行をtbodyに追加
        tbody.appendChild(newRow);
    });
});
