<template>
  <div class="pred-container">
    <div class="left">
        <div class="title">
          <img src="../assets/logo.png" style="width:80px;height:80px;" alt="">
           病情初步预测
        </div>
       <div class="form">
        <div class="form-group">
          <div class="form-label">
            病情描述
          </div>
          <div class="form-control">
            <input type="text" v-model="formSubmit.content">
          </div>
        </div>
        <div class="form-group button">
          <button type="button" style="cursor:pointer;" @click="submit">
            提交
          </button>
        </div>
       </div>
    </div>
    <div class="right">
      <div class="top">
        
            <div class="content">
              <div class="title">
                <dv-decoration-11 style="width:400px;height:60px;font-size:13px">小贴士：仅为机器预测，身体如有任何不适请到正规医院检查</dv-decoration-11>
              </div>
              
            </div>
       
      </div>
      <div class="top bottom">
        
            <div class="content">
              <div class="title">
                <dv-decoration-11 style="width:400px;height:60px;font-size:13px">预测结果</dv-decoration-11>

              </div>
             <dv-border-box-9>
              <div class="word" style="display:flex;justify-content:center;align-items:center;height:80px;font-size:35px">{{resultData}}</div>
             </dv-border-box-9>
            </div>
      
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'Pred',
  data(){
    return {
      formSubmit:{
        content:""
      },
      resultData:"暂无信息"
    }
  },
  created(){

  },
  methods:{
   async submit(){
    console.log(this.formSubmit);
    const res = await this.$http.post('./submitModel',this.formSubmit)
    console.log(res);
    this.resultData = res.data.resultData
   }
  },
  components: {
    
  }
}
</script>

<style lang="less" scoped>
  .button{
    width: 100%;
    height: 30px;
    display: flex;
    justify-content: center;
  }
  button{
    width: 80%;
    height: 100%;
    background: #26fffd;
    color:rgb(0, 0, 0);
    border-radius: 15px;
    
  }
  .pred-container{
    display: flex;
    width: 100%;
    height: 100vh;
    .left{
      width: 800px;
      display: flex;
      flex-direction: column;
      align-items: center;
      .title{
        color:#26fffd;
        margin-top: 80px;
        font-size: 38px;
        font-weight: bold;
      }
      .form{
        margin-top: 35px;
        .form-group{
          display: flex;
          align-items: center;
          margin-bottom: 15px;
          .form-label{
            margin-right: 25px;
            font-size: 18px;
            color:#fff;
          }
          .form-control input{
            border-radius: 15px;
            background: #d3dcf7;
            border: none;
            outline: none;
            padding: 0 5px;
            height: 25px;
            width: 200px;
          }
          .form-control select{
            border-radius: 15px;
            background: #d3dcf7;
            border: none;
            outline: none;
            padding: 0 5px;
            height: 25px;
            width: 210px;
          }
        }
      }
    }
    .right{
      flex: 1;
      .top{
        margin-top: 30px;
        width: 80%;
        // height: 500px;
        .content{
          padding:15px 25px;
          .title{
            display: flex;
            justify-content: center;
            color:#fff;
            font-weight: bold;
            font-size: 18px;
          }
          .word{
            font-size: 20px;
            color:orange;
            margin-top:15px;
            padding:0 20px;
            background: linear-gradient(to right, orange, #26fffd);
            -webkit-background-clip: text; /* 使用文本作为背景剪辑 */
            color: transparent; /* 隐藏文字本身的颜色 */
            display: inline-block; /* 确保渐变应用在文字上 */
          }
        }
      }
      .bottom{
        margin-top: 30px;
        width: 80%;
        height: 200px;
      }
    }
  }
</style>
