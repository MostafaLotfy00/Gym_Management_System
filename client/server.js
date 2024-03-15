const mongoose= require('mongoose')
const dotenv= require('dotenv')
dotenv.config({path: './config.env'})

const app= require("./app");

mongoose.connect("mongodb+srv://dev-abdo:2711@cluster0.zgsnbxy.mongodb.net/?retryWrites=true&w=majority",
    {
        useNewUrlParser: true,
        useCreateIndex: true,
        useFindAndModify: false,
        useUnifiedTopology:true
    }).then(con => console.log("Connecting to database..."))

//     mongoose.connect('mongodb://localhost:27017/test',
//  {
//      useNewUrlParser: true,
//      useUnifiedTopology: true})
//   .then(() => console.log('Connected to database...'))
//   .catch(error => console.error('Error connecting to MongoDB', error));


// console.log(process.env)
const port= process.env.PORT ||  3001
app.listen(port, ()=> console.log(`Listinning on port ${port}...`))