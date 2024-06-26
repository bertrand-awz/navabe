const sha256 = CryptoJS.SHA256;

//Interface Admin Pricipale
const Administration = {
    template: '#admin',
    name: 'Admin',

    data: () => {
        return {
            is_authentified: false,
            commands_view: false,
            set_new_admin: false,
            id: "",
            pass: "",
            books_result: [],
            search_keyword: "",
            invalid_ids_msg: ""
        }
    },
    methods: {
        check_logged: function () {
            const data = new URLSearchParams();
            admin_cookies = $cookies.get('crt-admin-infos');
            admin_cookies == null ? this.is_authentified = false : data.append('id', admin_cookies);
            console.log(data)
            fetch('/administration/check-session', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    this.is_authentified = data.status;
                })
        },
        books_search() {
            event.preventDefault();
            const data = new URLSearchParams();
            data.append('keyword', this.search_keyword);

            fetch('/administration/get-books', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    this.books_result = data;
                })
        },
        login() {
            event.preventDefault();
            const data = new URLSearchParams();

            data.append('id', this.id);
            data.append('password', sha256(this.pass).toString());

            fetch('/administration/admin-login', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    if (data.connected) {
                        this.is_authentified = data.connected;
                        this.firstname = data.firstname;
                        $cookies.set('crt-admin-infos', JSON.stringify([this.id]));
                        this.id = undefined;
                        this.pass = undefined;
                    }
                    else {
                        this.invalid_ids_msg = "Wrong ID or password";
                    }
                })

        },
        get_new_password(){
            event.preventDefault();
            data = new URLSearchParams();
            data.append('id', this.id)

            fetch('/administration/set_new_password_to_admin', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    if(data.op_success){
                        alert("A new password has been assigned to you.\n\n"+ 
                              "An email containing it has been sent to you,\n" +
                              "please check it and log in.\n\nThank you.");
                    }
                    else{
                        alert("Sorry, we were unable to provide you with a new password.\n"+
                              "Please make sure that this adminID is the one we sent you when you became an admin.\n\n"+
                              "Thank you");
                    }
                })
        }
    },
    mounted: function () {
        this.check_logged();
    }
}

//Recherches sur les commandes
const Search_Orders = {
    template:"#search_orders",
    name:'search_orders',

    data: ()=>{
        return{
            was_found  : false,
            switch_to_clientID: false,
            order_contents : [],
            order_infos: [],
            order_id:"",
        }
    },

    methods:{
        check_logged:()=>{
            const data = new URLSearchParams();
            admin_cookies = $cookies.get('crt-admin-infos');
            admin_cookies == null ? this.is_authentified = false : data.append('id', admin_cookies);


            fetch('/administration/check-session', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    this.is_authentified = data.status;

                    if (!this.is_authentified) {
                        this.$router.push('/')
                    }
                })
        },

        search_order(){
            const order_infos = new URLSearchParams();
            order_infos.append('orderID', this.order_id);

            fetch('/administration/search_command',{
                method:"POST",
                body:order_infos
            })
            .then(response => response.json())
            .then(data => {
                if(data.length > 0){
                    this.order_infos = data[0];
                    this.order_contents = data[1];
                }
            })
        },

    },

    watch:{
        order_id(newValue){
            if (this.order_id.length == 16){
                this.search_order()
            }
        },
        order_infos(newValue){
            if(this.order_infos.length > 0 && this.order_contents.length > 0){
                this.was_found = true
            }
        },

    },
    mounted: function(){
        this.check_logged();
    }
}

//Ajout d'un nouvel administrateur
const New_Admin = {
    template: '#set_admin',
    name: 'set_admin',

    data: () => {
        return {
            name: "",
            first_name: "",
            mail: "",
            is_authentified: false,
            quit: false,
            mail_error: "",
        }
    },
    methods: {

        check_logged: function () {
            const data = new URLSearchParams();
            admin_cookies = $cookies.get('crt-admin-infos');
            admin_cookies == null ? this.is_authentified = false : data.append('id', admin_cookies);

            //console.log(data)

            fetch('/administration/check-session', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    this.is_authentified = data.status;

                    if (!this.is_authentified) {
                        this.$router.push('/')
                    }
                })
        },

        register_admin() {
            
            const data = new URLSearchParams();

            if (this.name.length > 0 &&
                this.first_name.length > 0 &&
                this.mail.length > 0) {

                data.append('name', this.name);
                data.append('firstname', this.first_name);
                data.append('mail', this.mail);
                data.append('id', $cookies.get('crt-admin-infos')[0])

                fetch('/administration/New_Admin', {
                    method: "POST",
                    body: data
                })
                    .then(response => response.json())
                    .then(data => {
                        data.op_success == false ? this.mail_error = "existing e-mail" :
                            this.quit = true;
                            if (this.quit) {
                            this.$router.push('/');
            }
                    });

            };
            
        
        }

    },
    mounted: function () {
        this.check_logged();
    }
}

//Gestion des livres
const Books_Settings = {
    template: "#books-settings",

    data: () => {
        return {
            is_authentified: false,
            ISBN: "",
            title: "",
            year: "",
            price: "",
            author: "",
            editor: "",
            img_URL: "",
            category: "",
            synopsis: "",
            quantity: 1,
            switch_to_remove: false,
            book_exists: false,

        }
    },

    computed: {
        action() {

            return this.book_exists ? "Modify" : "Add";
        }
    },

    watch: {

        switch_to_remove(newValue) {
            if (newValue) {
                this.reset_all(op_isbn = true);
            }
        },

        ISBN(newValue) {
            if (this.ISBN.length == 13) {
                this.search_book();
            }
            else {
                this.reset_all();
            }

        }
    },

    methods: {
        reset_all(op_isbn = false) {

            if (op_isbn) {
                this.ISBN = "";
            }
            this.book_exists = false;
            this.title = "";
            this.price = "";
            this.author = "";
            this.year = "";
            this.editor = "";
            this.category = "";
            this.synopsis = "";
            this.img_URL = "";

        },
        search_book() {
            const data = new URLSearchParams();
            data.append('keyword', this.ISBN);

            fetch('/administration/get-books', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    if (data.length == 1) {

                        const book = data[0];

                        this.book_exists = true;

                        this.title = book.title;
                        this.year = book.year;
                        this.price = book.price;
                        this.author = book.author;
                        this.editor = book.editor;
                        this.img_URL = book.url_img;
                        this.category = book.category;
                        this.synopsis = book.synopsis;

                    }
                })
            console.log('OK');
        },

        check_logged: function () {
            const data = new URLSearchParams();
            admin_cookies = $cookies.get('crt-admin-infos');
            admin_cookies == null ? this.is_authentified = false : data.append('id', admin_cookies);

            fetch('/administration/check-session', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    this.is_authentified = data.status;

                    if (!this.is_authentified) {
                        this.$router.push('/')
                    }
                })
        },
        add_or_modify() {

            data = new URLSearchParams();

            data.append('isbn', this.ISBN)
            data.append('title', this.title)
            data.append('author', this.author)
            data.append('category', this.category)
            data.append('synopsis', this.synopsis)
            data.append('p_year', this.year)
            data.append('price', this.price)
            data.append('editor', this.editor)
            data.append('img_link', this.img_URL)
            data.append('qty', this.quantity)
            data.append('id', $cookies.get('crt-admin-infos')[0])

            fetch('/administration/add_modif_book', {
                method: "POST",
                body : data
            })
                .then(response => response.json())
                .then(data => {
                    msg = this.action == "Add" ? "New book inserted successfully":
                                                   "Information of the book successfully modified";
                    if (data.op_success){
                        this.reset_all(true);
                        alert(msg);
                    } else {
                        alert("An error has occurred");
                    }
                })
        },
        drop_book(){
            data = new URLSearchParams();
            data.append('id',$cookies.get('crt-admin-infos')[0])
            data.append('isbn', this.ISBN)

            fetch('/administration/drop_book', {
                method : "POST",
                body: data
            })
            .then(response => response.json())
            .then(data =>{
                if(data.op_success){
                    this.reset_all(true);
                    alert("Successful removal");
                }
                else{
                    alert("An error has occurred");
                }
            })

        },
        
    },

    mounted: function () {
        this.check_logged();
    }
}

//Statistiques de la librairie,
//Les graphiques sont réalisés avec Chart.JS
const DataVisualisation = {
    template : '#stat',
    name: 'DataVisualisation',

    data:() =>{
        return{
            is_authentified: false,
            choice_ss : "s", //pour stat_stock
            choice_sv : "m", //pour stat_sales
            choice_sa : "c", //pour stat_average

            stat_stock :[],   //caller: 'osi' => 'Our Stock Items'
            stat_vente :[] ,  //caller: 'osl' => 'Our SaLes'
            stat_avg : []    //caller: 'oap' => 'Our average prices'

        }
    },

    methods: {
        check_logged: function () {
            const data = new URLSearchParams();
            admin_cookies = $cookies.get('crt-admin-infos');
            admin_cookies == null ? this.is_authentified = false : data.append('id', admin_cookies);

            fetch('/administration/check-session', {
                method: "POST",
                body: data
            })
                .then(response => response.json())
                .then(data => {
                    this.is_authentified = data.status;

                    if (!this.is_authentified) {
                        this.$router.push('/')
                    }
                })
        },
        get_statData(option='', appelant="osi"){
            demand = new URLSearchParams();
            demand.append('caller', appelant);
            demand.append('option', option);

            fetch('/administration/get_data_for_stat',{
                method:"POST",
                body: demand
            })
                .then(response => response.json())
                .then(data=>{
                    appelant == 'osi' ? this.Stat_stock_Chart(data) : 
                        (appelant == 'osl' ? this.Stat_sales_Chart(data):
                            (appelant == 'oap' ? this.Stat_Average_Chart(data):
                                appelant == 'ort'? this.Stat_OrderStatus_Chart(data):
                                    alert('Invalid arguments have been made')));
                })
        },
        Stat_stock_Chart(data_) {
            //Graphique Stock 
            const stock_Chart = this.$refs.stat_stock.getContext('2d');

            if(this.StockGraph != null){
                this.StockGraph.destroy();
            }
            const data = {
                labels : data_.labels,
                datasets : [{
                    label:'',
                    data : data_.values, //Nombre de livres par catégorie 
                    backgroundColor:data_.colors, //Liste des couleurs 
                    
                }]
            };
            
            const options={
                onClick:(event, chartElement)=>{
                    if (chartElement.length > 0) {
                      var dataIndex = chartElement[0].index;
                      this.StockGraph.data.datasets[0].data.splice(dataIndex, 1);
                      this.StockGraph.data.labels.splice(dataIndex,1)
                      this.StockGraph.update();
                    }
                  },
                  plugins : {
                    legend:{
                        display:false
                    }
                  },
                scales:{
                    y:{
                        title:{
                            display : true,
                            text : 'Quantity',
                            color : 'black',
                            font:{
                                family:"Times",
                                size: 15
                            }
                        },
                    },
                    x:{
                        title:{
                            display : true,
                            text : typeof(data.labels[0]) == "number" ? "Year": "Category",
                            color : 'black',
                            font:{
                                family:"Times",
                                size: 15
                            }
                        }
                    }
                }
            };
            this.StockGraph= new Chart(stock_Chart, {
              type: 'bar',
              data: data,
              options: options
            });
          },

        Stat_sales_Chart(data_){
            //Graphique de ventes
            const salesChart = this.$refs.stat_sales.getContext('2d');

            if(this.SalesGraph != null){
                this.SalesGraph.destroy();
            }

            const data = {
                labels : data_.labels,
                datasets : [
                    {
                        data: data_.values,
                        borderColor : '#007566',
                        backgroundColor: "#007566",
                        fill: false,
                        label : 'Total earning per month',
                        lineTension:0
                    }
                ]
            }

            const options = {
                scales : {
                    
                    y:{
                        title:{
                            display: true,
                            text:'Incoming flows in dollars\n [Per thousand]',
                            color: 'Black',
                            font:{
                                family:"Times",
                                size : 15
                            }
                        },
                        min: 0,
                        max : 10,
                        ticks:{
                            stepSize:1
                        }
                        
                    },
                    x:{
                        title:{
                            display: true,
                            text: 'Month',
                            color: 'Black',
                            font:{
                                family:"Times",
                                size : 15
                            }
                        }
                        
                    }
                }
            }

            this.SalesGraph = new Chart(salesChart,{
                type: 'line',
                data : data,
                options: options
            });
        },

        Stat_Average_Chart(data_){
            //Graphique pour les moyennes
            const averageChart = this.$refs.stat_average.getContext('2d');

            if(this.AverageGraph != null){
                this.AverageGraph.destroy();
            }

            const data = {
                labels : data_.labels,
                datasets : [{
                    data : data_.values,
                    backgroundColor : data_.colors
                }]
            };

            const options = {
                
                onClick:(event, chartElement)=>{
                    if (chartElement.length > 0) {
                      var dataIndex = chartElement[0].index;
                      this.AverageGraph.data.datasets[0].data.splice(dataIndex, 1);
                      this.AverageGraph.data.labels.splice(dataIndex,1)
                      this.AverageGraph.update();
                    }
                  },
                  plugins : {
                    legend:{
                        display:false
                    }
                  },
                  scales: {
                        y:{
                            title:{
                                display : true,
                                text : 'Price in dollars',
                                color : 'black',
                                font:{
                                    family:"Times",
                                    size: 15
                                }
                            },

                            min :0,
                            max : 45,
                            ticks: {
                                stepSize : 3,
                            }
                        },
                        x:{
                            title:{
                                display : true,
                                text : typeof(data.labels[0]) == "number" ? "Year": "Category",
                                color : 'black',
                                font:{
                                    family:"Times",
                                    size: 15
                                }
                            }
                        }
                  }
            };

            this.AverageGraph= new Chart(averageChart,{
                type : 'bar',
                data : data,
                options : options,
            })
        },
        Stat_OrderStatus_Chart(data_){
            //Graphique répresentatif des commandes

            const order_Chart = this.$refs.order_status.getContext('2d');

            if(this.OrderGraph != null){
                this.OrderGraph.destroy();
            }

            const data = {
                labels : data_.labels,
                datasets:[{
                    data: data_.values,
                    backgroundColor:data_.colors,
                    hoverOffset: 4
                }]
            };

            const options = {
                responsive : false,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            pointStyle: 'circle',
                            color:'black'
                        }
                    }
                }
            };

            this.OrderGraph = new Chart(order_Chart, {
                type : 'pie',
                data : data,
                options: options
            })
        }
        
    },

    watch:{
        choice_ss(newValue){
            //Demande de changement de données à afficher (De la part de "Our stock Items")
            this.get_statData(newValue, "osi");
        },
        choice_sa(newValue){
            this.get_statData(newValue, "oap")
        }
    },

    mounted: function () {
        //A la monture, on demande au serveur de chercher ses infos dans la BDD
        this.check_logged();
        this.get_statData(this.choice_ss, "osi");
        this.get_statData('','osl')
        this.get_statData('r', 'ort')
        this.get_statData(this.choice_sa, "oap");

    }
}

const routes = [
    { path: '/', component: Administration },
    { path: '/books-settings', component: Books_Settings },
    { path: '/register-new-admin', component: New_Admin },
    { path: '/statistics', component: DataVisualisation},
    { path: '/orders', component: Search_Orders}
]

const router = VueRouter.createRouter({
    history: VueRouter.createWebHashHistory(),
    routes
})

const app = Vue.createApp({})
app.config.compilerOptions.delimiters = ['${', '}']
app.use(router)
app.mount('#app')