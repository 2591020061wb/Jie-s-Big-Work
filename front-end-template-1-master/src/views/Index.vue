<template>
  <div class="home">
    <transition name="fade" mode="out-in">
      <dv-loading v-if="!config4.data.length">Loading...</dv-loading>
      <dv-border-box-10>
        <div class="naca">
          <div class="index-header" style="margin-top: 5px">
            <div>
              <dv-decoration-10 style="width: 450px; height: 1px; margin-bottom: 45px" />
              <dv-decoration-8 style="width: 180px; height: 50px" :color="['#568aea', '#000000']" />
              <div
                style="
                  width: 150px;
                  color: #eeecec;
                  font-size: 18px;
                  padding: 0 15px;
                  font-weight: bold;
                "
              >
                可视化化平台
              </div>
              <dv-decoration-8
                :reverse="true"
                style="width: 180px; height: 50px"
                :color="['#568aea', '#000000']"
              />
              <dv-decoration-10
                style="
                  width: 450px;
                  height: 1px;
                  transform: rotateY(180deg);
                  margin-bottom: 45px;
                "
              />
            </div>
            <dv-decoration-5 style="width: 10%; height: 20px" :color="['#568aea', '#000000']" />
          </div>

          <div class="index-content">
            <div class="left">
              <div class="left-1">
                <dv-border-box-12>
                  <div style="padding: 5px">
                    <div class="title" style="margin-top: 5px">各年龄段患病占比</div>
                    <div ref="firstMain" style="width: 100%; height: 120px"></div>
                  </div>
                </dv-border-box-12>

                <dv-border-box-8>
                  <div style="padding: 5px; padding-bottom: 30px">
                    <div class="title" style="margin-top: 1px">疾病类型分布</div>
                    <dv-capsule-chart :config="config1" style="width: 80%; height: 110px" />
                  </div>
                </dv-border-box-8>

                <dv-border-box-3>
                  <div style="padding: 15px">
                    <div class="title" style="margin-top: 5px">病例列表</div>
                    <div class="row_list">
                      <ul class="cases_list" style="width: 100%; height: 159px; overflow: auto">
                        <li style="font-size: 15px">
                          <div>编号</div>
                          <div>求诊类型</div>
                          <div>性别</div>
                          <div>年龄</div>
                          <div>身高</div>
                          <div>体重</div>
                          <div>患病时长</div>
                        </li>
                        <li v-for="cases in casesData" :key="cases[0]">
                          <div>{{ cases[0] }}</div>
                          <div>{{ cases[1] }}</div>
                          <div>{{ cases[2] }}</div>
                          <div>{{ cases[3] }}</div>
                          <div>{{ cases[10] }}</div>
                          <div>{{ cases[11] }}</div>
                          <div>{{ cases[12] }}</div>
                        </li>
                      </ul>
                    </div>
                  </div>
                </dv-border-box-3>
              </div>
            </div>

            <div class="cents">
              <div class="above">
                <div class="aboveOne">
                  <div style="padding: 15px">
                    <div class="title">疾病数据信息</div>
                    <div
                      style="
                        display: flex;
                        flex-direction: column;
                        width: 100%;
                        height: 120px;
                        color: #eeecec;
                      "
                    >
                      <div style="display: flex; flex: 1">
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">数据数量:{{ centerData.maxNum }}</div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">最多疾病类型:{{ centerData.maxType }}</div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">求诊最多科室:{{ centerData.maxDep }}</div>
                        </dv-decoration-11>
                      </div>
                      <div style="display: flex; flex: 1">
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">最大患者年龄:{{ centerData.maxAge }}</div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">最小患者年龄:{{ centerData.minAge }}</div>
                        </dv-decoration-11>
                        <dv-decoration-11 style="height: 60px; text-align: center">
                          <div style="flex: 1">热门医院:{{ centerData.maxHos }}</div>
                        </dv-decoration-11>
                      </div>
                    </div>
                  </div>

                  <div style="padding: 15px">
                    <div class="title" style="margin-top: -30px">男女性别患病对比</div>
                    <div class="content">
                      <dv-active-ring-chart :config="config3" style="width: 150px; height: 100px" />
                      <dv-water-level-pond :config="config4" style="width: 100px; height: 90px" />
                      <dv-active-ring-chart :config="config3" style="width: 150px; height: 100px" />
                    </div>
                  </div>
                </div>

                <div class="aboveTwo">
                  <dv-border-box-9 :color="['#568aea']">
                    <div style="padding: 15px">
                      <div class="title" style="margin-top: 5px">医院科室环形图</div>
                      <div
                        id="secondMian"
                        ref="secondMain"
                        style="width: 100%; height: 110px"
                      ></div>
                    </div>
                  </dv-border-box-9>

                  <dv-border-box-1>
                    <div style="padding: 5px">
                      <div class="title" style="margin-top: 5px">疾病关键词云图</div>
                      <div ref="thirdMain" style="width: 400px; height: 90px"></div>
                    </div>
                  </dv-border-box-1>
                </div>
              </div>

              <div class="below">
                <dv-border-box-13>
                  <div style="padding: 7px">
                    <div class="title" style="margin-top: 5px">患病身高体重平均数图</div>
                    <div
                      ref="lastMain"
                      style="width: 100%; height: 200px; margin-top: 25px"
                    ></div>
                  </div>
                </dv-border-box-13>
              </div>
            </div>
          </div>
        </div>
      </dv-border-box-10>
    </transition>
  </div>
</template>

<script>
function formatter(number) {
  const numbers = number.toString().split("").reverse();
  const segs = [];
  while (numbers.length) segs.push(numbers.splice(0, 3).join(""));
  return segs.join(",").split("").reverse().join("");
}

export default {
  name: "Index",
  data() {
    return {
      currentIndex: 0,
      pieData: [],
      casesData: [],
      centerData: {
        maxNum: "",
        maxType: "",
        maxDep: "",
        maxHos: "",
        maxAge: "",
        minAge: "",
      },
      wordData: [],
      circleData: [],
      lastData: {
        xData: [],
        y1Data: [],
        y2Data: [],
      },
      config1: {},
      config2: {
        lineWidth: 20,
        radius: "50%",
        activeRadius: "60%",
        activeTimeGap: 2000,
        digitalFlopStyle: { fontSize: 13 },
        data: [{ name: "demo", value: 1 }],
      },
      config3: {
        lineWidth: 20,
        radius: "50%",
        activeRadius: "60%",
        activeTimeGap: 2000,
        digitalFlopStyle: { fontSize: 13 },
        data: [],
      },
      config4: {
        data: [],
        shape: "roundRect",
      },
      chartInstances: {
        agePie: null,
        wordCloud: null,
        deptRing: null,
        hwChart: null,
      },
      timers: [],
    };
  },
  methods: {
    async loadHomeData() {
      const res = await this.$http.get("/getHomeData");
      const data = res.data || {};
      this.pieData = data.pieData || [];
      this.config1.data = data.configOne || [];
      this.casesData = data.casesData || [];
      this.centerData.maxNum = data.maxNum || "";
      this.centerData.maxType = data.maxType || "";
      this.centerData.maxDep = data.maxDep || "";
      this.centerData.maxHos = data.maxHos || "";
      this.centerData.maxAge = data.maxAge || "";
      this.centerData.minAge = data.minAge || "";
      this.circleData = data.circleData || [];
      this.wordData = data.wordData || [];
      this.lastData = data.lastData || { xData: [], y1Data: [], y2Data: [] };
      this.config2.data = data.boyList || [];
      this.config3.data = data.girlList || [];
      this.config4.data = data.ratioData || [];
    },
    startTimers() {
      this.clearTimers();
      this.timers.push(
        setInterval(() => {
          this.setPieData();
          this.setConfig1();
          this.setWordData();
        }, 1000)
      );
      this.timers.push(
        setInterval(() => {
          this.setCircleData();
        }, 3000)
      );
      this.timers.push(
        setInterval(() => {
          this.setLastData();
        }, 2000)
      );
    },
    clearTimers() {
      this.timers.forEach((timer) => clearInterval(timer));
      this.timers = [];
    },
    disposeCharts() {
      Object.keys(this.chartInstances).forEach((key) => {
        if (this.chartInstances[key]) {
          this.chartInstances[key].dispose();
          this.chartInstances[key] = null;
        }
      });
    },
    getChartInstance(key, dom) {
      if (!dom) return null;
      if (!this.chartInstances[key]) {
        this.chartInstances[key] = this.$echarts.init(dom);
      }
      return this.chartInstances[key];
    },
    setPieData() {
      if (!this.pieData.length) return;
      const chartDom = this.$refs.firstMain;
      const myChart = this.getChartInstance("agePie", chartDom);
      if (!myChart) return;
      const option = {
        tooltip: { trigger: "item", formatter: "{a} <br/>{b}:{c} ({d}%)" },
        legend: {
          orient: "vertical",
          icon: "circle",
          left: 0,
          data: this.pieData.map((item) => item.name),
          textStyle: { color: "#fff" },
        },
        series: [
          {
            name: "年龄占比",
            type: "pie",
            radius: [20, 50],
            roseType: "area",
            center: ["50%", "55%"],
            label: { show: true },
            emphasis: {
              itemStyle: {
                shadowBlur: 10,
                shadowOffsetX: 0,
                label: { show: true, fontWeight: "bold" },
              },
            },
            data: this.pieData,
          },
        ],
      };
      myChart.setOption(option);
      myChart.dispatchAction({
        type: "downplay",
        seriesIndex: 0,
        dataIndex: this.currentIndex,
      });
      this.currentIndex = (this.currentIndex + 1) % this.pieData.length;
      myChart.dispatchAction({
        type: "highlight",
        seriesIndex: 0,
        dataIndex: this.currentIndex,
      });
    },
    changeData(arr = []) {
      if (!Array.isArray(arr) || arr.length < 2) return arr;
      const first = arr.shift();
      arr.push(first);
      return arr;
    },
    getSeriesData() {
      const series = [];
      const source = Array.isArray(this.circleData) ? this.circleData : [];
      source.forEach((item, index) => {
        if (index < 5) {
          series.push({
            name: item.name,
            type: "pie",
            clockWise: false,
            hoverAnimation: false,
            radius: [73 - index * 15 + "%", 68 - index * 15 + "%"],
            center: ["50%", "50%"],
            label: { show: false },
            data: [
              { value: item.value, name: item.name },
              {
                value: 3,
                itemStyle: { color: "rgba(0,0,0,0)", borderWidth: 0 },
                tooltip: { show: false },
                hoverAnimation: false,
              },
            ],
          });
        }
      });
      return series;
    },
    randomColor() {
      const r = Math.floor(Math.random() * 255);
      const g = Math.floor(Math.random() * 255);
      const b = Math.floor(Math.random() * 255);
      return `rgb(${r},${g},${b})`;
    },
    setWordData() {
      if (!this.wordData.length) return;
      const chartDom = this.$refs.thirdMain;
      const myChart = this.getChartInstance("wordCloud", chartDom);
      if (!myChart) return;
      const option = {
        series: {
          type: "wordCloud",
          sizeRange: [20, 40],
          gridSize: 0,
          rotationRange: [0, 0],
          layoutAnimation: true,
          textStyle: { color: this.randomColor },
          emphasis: { textStyle: { fontWeight: "bold", color: "#fff" } },
          data: this.wordData,
        },
      };
      myChart.setOption(option);
    },
    setCircleData() {
      if (!this.circleData.length) return;
      const newData = [...this.circleData];
      this.changeData(newData);
      this.circleData = newData;
      const chartDom = this.$refs.secondMain || document.getElementById("secondMian");
      const myChart = this.getChartInstance("deptRing", chartDom);
      if (!myChart) return;
      const option = {
        legend: {
          show: true,
          icon: "circle",
          top: "8%",
          left: "10%",
          data: this.circleData.map((item) => item.name),
          itemWidth: 10,
          itemHeight: 10,
          itemGap: 6,
          textStyle: { fontSize: 12, color: "#ffffff" },
        },
        tooltip: { show: true, trigger: "item", formatter: "{b}<br>{c}({d}%)" },
        series: this.getSeriesData(),
      };
      myChart.setOption(option);
    },
    setLastData() {
      const data = this.lastData;
      if (
        !data ||
        !Array.isArray(data.xData) ||
        !Array.isArray(data.y1Data) ||
        !Array.isArray(data.y2Data)
      ) {
        return;
      }
      this.changeData(data.xData);
      this.changeData(data.y1Data);
      this.changeData(data.y2Data);
      const chartDom = this.$refs.lastMain;
      const myChart = this.getChartInstance("hwChart", chartDom);
      if (!myChart) return;
      const option = {
        tooltip: {
          trigger: "axis",
          backgroundColor: "rgba(255,255,255,0.1)",
          axisPointer: {
            type: "shadow",
            label: { show: true, backgroundColor: "#7B7DDC" },
          },
        },
        dataZoom: [{ type: "slider", start: 0, end: 80, show: false }],
        legend: {
          data: ["身高", "体重"],
          textStyle: { color: "#B4B4B4" },
          top: "0%",
        },
        grid: { x: "8%", width: "85%", height: "87%", y: "4%" },
        xAxis: {
          data: data.xData,
          axisLine: { lineStyle: { color: "#B4B4B4" } },
          axisLabel: { show: true, interval: 0 },
          axisTick: { show: false },
        },
        yAxis: [
          {
            splitLine: { show: false },
            axisLine: { lineStyle: { color: "#B4B4B4" } },
            axisLabel: { formatter: "{value} " },
          },
          {
            splitLine: { show: false },
            axisLine: { lineStyle: { color: "#B4B4B4" } },
            axisLabel: { formatter: "{value} " },
          },
        ],
        series: [
          {
            name: "身高",
            type: "line",
            smooth: true,
            showAllSymbol: true,
            symbol: "emptyCircle",
            symbolSize: 8,
            yAxisIndex: 1,
            itemStyle: {
              normal: {
                barBorderRadius: 5,
                color: new this.$echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: "#5C4033" },
                  { offset: 1, color: "#FAEBD7" },
                ]),
              },
            },
            data: data.y1Data,
          },
          {
            name: "体重",
            type: "bar",
            barWidth: "60%",
            itemStyle: {
              normal: {
                barBorderRadius: 5,
                color: new this.$echarts.graphic.LinearGradient(0, 0, 0, 1, [
                  { offset: 0, color: "#082e53" },
                  { offset: 1, color: "white" },
                ]),
              },
            },
            data: data.y2Data,
          },
        ],
      };
      myChart.setOption(option);
    },
    setConfig1() {
      if (!Array.isArray(this.config1.data) || !this.config1.data.length) return;
      const newData = [...this.config1.data];
      this.changeData(newData);
      this.config1 = { data: newData, showValue: true };
    },
  },
  async mounted() {
    await this.loadHomeData();
    this.$nextTick(() => {
      this.setPieData();
      this.setConfig1();
      this.setWordData();
      this.setCircleData();
      this.setLastData();
      this.startTimers();
    });
  },
  beforeDestroy() {
    this.clearTimers();
    this.disposeCharts();
  },
};
</script>




<style lang="less" scoped>
.loading {
  position: absolute;
  left: 50%;
  top: 50%;
  transform: translate(-50%, -50%);
}
.cent-1-content {
  padding: 20px;
  display: flex;
}
.right-content {
  margin-left: 30px;
  display: flex;
  flex-direction: column;
  justify-content: space-around;
}
.right-content div {
  display: flex;
  font-size: 15px;
  align-items: center;
}
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.5s;
}
.fade-enter,
.fade-leave-to {
  opacity: 0;
}
.cents {
  display: flex;
  flex-direction: column;
}
.above {
  display: flex;
}
.aboveOne {
  display: flex;
  flex-direction: column;
}
.aboveTwo {
  display: flex;
  flex-direction: column;
}
.cent {
  width: 850px;
  height: 300px;
}

.cent-1 {
  margin: 10px;
  color: aliceblue;
  width: 500px;
  height: 220px;
  /* background-color: rgb(26, 26, 133); */
}

.left {
  display: flex;
  flex-direction: column;
}

.left-1 {
  margin: 15px;
  color: aliceblue;
  width: 550px;
  display: flex;
  flex-direction: column;
}
.left-2 {
  margin: 15px;
  color: aliceblue;
  width: 530px;
  display: flex;
  flex-direction: column;
}

.naca {
  // padding: 35px 15px 0 15px;
  box-sizing: border-box;
  width: 100%;
  // height: 40rem;
  display: flex;
  flex-direction: column;
}
.naca .index-header {
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}
.naca .index-header div {
  display: flex;
  justify-content: center;
  align-items: center;
}
.naca .index-content {
  display: flex;
  justify-content: center;
  align-items: center;
}
.bg {
  width: 100%;
  height: 45rem;
  background-color: black;
  position: relative;
}
.title {
  color: #3f96a5;
  font-size: 18px;
  margin-top: -20px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
  font-weight: bold;
}
.content {
  display: flex;
  align-items: center;
}
.content-word {
  width: 140px;
  height: 130px;
  background: #11193e;
  border-radius: 40px;
  border: 1px solid #3d3d3d;
  display: flex;
  flex-direction: column;
  justify-content: center;
}
.content-word-item {
  margin-left: 19px;
  margin-bottom: 10px;
  img {
    width: 20px;
    height: 20px;
  }
}
.content-word-item-title {
  font-size: 18px;
}
.content-word-item-content {
  margin-top: 5px;

  display: flex;
  align-items: center;
}
.row_list {
  list-style: none;
}
.cases_list::-webkit-scrollbar {
  display: none;
}

.cases_list li {
  display: grid;
  -ms-grid-columns: 30px 110px 60px 60px 60px 50px 100px;
  grid-template-columns: 30px 110px 60px 60px 60px 50px 100px;
  cursor: pointer;
  margin-left: 23px;
  text-align: center;
  line-height: 30px;
  color: rgb(238, 236, 236);
}
.list_time {
  height: 30px;
  overflow: auto;
}
.list_time::-webkit-scrollbar {
  display: none;
}
</style>