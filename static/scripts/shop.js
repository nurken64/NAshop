document.addEventListener("DOMContentLoaded", function() {
    var categoryList = document.getElementById("category-list");
    var productList = document.getElementById("product-list");

    categoryList.addEventListener("click", function(event) {
        var categoryItems = categoryList.getElementsByTagName("li");
        for (var i = 0; i < categoryItems.length; i++) {
            categoryItems[i].classList.remove("active");
        }

        var clickedItem = event.target;
        clickedItem.classList.add("active");

        var selectedCategory = clickedItem.dataset.category;

        var productItems = productList.getElementsByTagName("li");
        for (var j = 0; j < productItems.length; j++) {
            var productItem = productItems[j];

            if (selectedCategory === "all" || productItem.dataset.category === selectedCategory) {
                productItem.style.display = "block";
            } else {
                productItem.style.display = "none";
            }
        }
    });
});

function addToCart(productId) {
    var xmlreq = new XMLHttpRequest();

    var url = '/add_to_cart';

    var params = 'product_id=' + encodeURIComponent(productId);

    xmlreq.open('POST', url, true);
    xmlreq.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');

    xmlreq.onload = function() {
      if (xmlreq.status === 200) {
        var cartCount = document.getElementById('cart-count');
        var currentCount = parseInt(cartCount.innerText);
        cartCount.innerText = currentCount + 1;


      } else {
        alert('Error adding item to a cart');
      }
    };

    xmlreq.send(params);
  }
