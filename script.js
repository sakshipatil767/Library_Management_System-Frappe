document.addEventListener("DOMContentLoaded", function () {   
    const bookList = document.getElementById("bookList");
    const searchInput = document.querySelector(".search-bar input");
    const searchButton = document.querySelector(".search-bar button");

    let allBooks = []; 

    async function fetchBooks() {
        try {
            const response = await fetch('jk.json');
            const data = await response.json();
            return data.message;
        } catch (error) {
            console.error('Error fetching books:', error);
            return [];
        }
    }
    function displayBooks(books) {
        bookList.innerHTML = "";
    
        books.forEach((book) => {
            const bookDiv = document.createElement("div");
            bookDiv.className = "book";
    
            bookDiv.innerHTML = `<h3>${book.title}</h3>
                <img src="vector.jpg" alt="${book.title} Image" class="book-image">
                <a class="button" href="detail.html?title=${encodeURIComponent(book.title)}">Show Details</a>`;
    
            bookList.appendChild(bookDiv);
        });
    }
    

    async function initialize() {
        allBooks = await fetchBooks();
        displayBooks(allBooks);
    }
    searchButton.addEventListener("click", function () {
        const searchTerm = searchInput.value.toLowerCase();
        const filteredBooks = allBooks.filter(book =>
            book.title.toLowerCase().includes(searchTerm) ||
            (book.author && book.author.toLowerCase().includes(searchTerm))
        );

        displayBooks(filteredBooks);
    });

    initialize(); 
});

