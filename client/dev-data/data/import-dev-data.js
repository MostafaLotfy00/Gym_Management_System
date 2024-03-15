const fs= require('fs')
const mongoose= require('mongoose')
const dotenv= require('dotenv')
dotenv.config({path: './config.env'})
// const Tour= require('./../../models/tourModel')
const Private= require('./../../models/privateSupscriptionModel')


mongoose.connect("mongodb+srv://dev-abdo:2711@cluster0.zgsnbxy.mongodb.net/?retryWrites=true&w=majority",
    {
        useNewUrlParser: true,
        useCreateIndex: true,
        useFindAndModify: false,
        useUnifiedTopology:true
    }).then(con => console.log("Connecting to database..."))

    
    const filePath= './privatess.json'

    const readData= async(req, res)=>{
       const data=JSON.stringify( await Private.find())
        console.log("data readed successfully")
        try {
            fs.writeFileSync(filePath, data);
            console.log('The file has been saved!');
          } catch (err) {
            console.error(err);
          }
    }
    readData()

    

// const importData= async()=>{
//     try{
//         await Tour.create(tours)
//         console.log("data successfully loaded")
//         process.exit()
//     }catch(err){
//         console.log(err.message)
//     }
// }

// const deleteData= async()=>{
//     try{
//         await Tour.deleteMany()
//         console.log("data deleted successfully")
//         process.exit()
//     }catch(err){
//         console.log(err.message)
//     }
// }

// if(process.argv[2] === "--import")
// {
//     importData()
// }else if(process.argv[2] === "--delete"){
//     deleteData()
// }


// console.log(process.argv)

