<template>
  <div class="tableData-container">
      <transition name="fade" mode="out-in">
        <dv-loading v-if="!config.data.length">
            loading
        </dv-loading>
        <div  v-else   class="content">
        <dv-scroll-board :config="config" style="width:85%;height:600px" />
        </div>
      </transition>
  </div>
</template>

<script>
export default {
    data(){
        return {
            config:{
                header: [],
                data: [],
                index: true,
                align: [],
                headerBGC:"#3077b1",
            },
            tableList:[]
        }
    },
    async created(){
        await this.delay(1500)
        this.getTableList()
    },
    methods:{
        delay(ms){
            return new Promise(resolve => setTimeout(resolve, ms));
        },
        async getTableList(){
            const res = await this.$http.get('/tableData')
            this.tableList = res.data.resultData
            this.config.header = ['类型','性别','年龄','时间','描述','求诊医生','求诊医院','类型求诊科室','详情链接','身高','体重','患病时间','过敏史']
            this.config.data = res.data.resultData
            this.config.align = this.config.header.map(item =>'center')
            this.config.align.push('center')
            console.log(this.config.data);
        }
    }
}
</script>

<style scoped>
.content{
    display: flex;
    justify-content: center;
}
    .fade-enter-active, .fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter, .fade-leave-to {
  opacity: 0;
}
</style>