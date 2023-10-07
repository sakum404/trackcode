// Получите элементы из DOM
const searchInput = document.getElementById("searchInput");
const searchHistorySelect = document.getElementById("searchHistorySelect");

function saveSearch() {
    const searchTerm = searchInput.value.trim();

    if (searchTerm) {
        // Получите текущую историю поиска из localStorage
        const history = JSON.parse(localStorage.getItem("searchHistory")) || [];

        // Проверьте, не существует ли уже такого поискового запроса
        if (!history.includes(searchTerm)) {
            // Добавьте новый поиск в историю
            history.push(searchTerm);

            // Сохраните обновленную историю в localStorage
            localStorage.setItem("searchHistory", JSON.stringify(history));

            // Обновите отображение истории поиска
            displaySearchHistory();
        }
    }
}

// Функция для отображения истории поиска в элементе <select>
function displaySearchHistory() {
    searchHistorySelect.innerHTML = "";
    const history = JSON.parse(localStorage.getItem("searchHistory")) || [];

    for (const searchTerm of history) {
        const option = document.createElement("option");
        option.text = searchTerm;
        searchHistorySelect.appendChild(option);
    }
}

// Вызовите функцию отображения истории поиска при загрузке страницы
displaySearchHistory();
