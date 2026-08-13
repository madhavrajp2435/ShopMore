const fileInput = document.getElementById("imageInput");
const preview = document.getElementById("preview");
const result = document.getElementById("result");

fileInput.addEventListener("change", () => {
    const file = fileInput.files[0];

    if (!file) {
        return;
    }

    preview.src = URL.createObjectURL(file);
    preview.style.display = "block";

    uploadImage(file);
});

async function uploadImage(file) {
    const formData = new FormData();

    formData.append("file", file);

    try {
        const response = await fetch("/analyze-image", {
            method: "POST",
            body: formData
        });

        const data = await response.json();

        result.textContent = JSON.stringify(data, null, 2);
    } catch (error) {
        alert(
            "ShopMore could not analyze the image.\n\n" +
            error.message
        );
    }
}