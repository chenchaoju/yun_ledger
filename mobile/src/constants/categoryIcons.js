import {
  Bowl,
  CoffeeCup,
  Coin,
  FirstAidKit,
  House,
  MoreFilled,
  OfficeBuilding,
  Phone,
  Present,
  Reading,
  Service,
  ShoppingBag,
  ShoppingCart,
  Suitcase,
  Trophy,
  Van,
  Wallet
} from '@element-plus/icons-vue'

export const categoryIconOptions = [
  { label: '餐饮', value: 'Bowl', component: Bowl },
  { label: '咖啡', value: 'CoffeeCup', component: CoffeeCup },
  { label: '交通', value: 'Van', component: Van },
  { label: '购物', value: 'ShoppingBag', component: ShoppingBag },
  { label: '网购', value: 'ShoppingCart', component: ShoppingCart },
  { label: '服务', value: 'Service', component: Service },
  { label: '居住', value: 'House', component: House },
  { label: '送礼', value: 'Present', component: Present },
  { label: '娱乐', value: 'Trophy', component: Trophy },
  { label: '医疗', value: 'FirstAidKit', component: FirstAidKit },
  { label: '教育', value: 'Reading', component: Reading },
  { label: '工资', value: 'Wallet', component: Wallet },
  { label: '金币', value: 'Coin', component: Coin },
  { label: '办公', value: 'OfficeBuilding', component: OfficeBuilding },
  { label: '通信', value: 'Phone', component: Phone },
  { label: '出差', value: 'Suitcase', component: Suitcase },
  { label: '其他', value: 'MoreFilled', component: MoreFilled }
]

export const categoryIconComponents = categoryIconOptions.reduce((map, item) => {
  map[item.value] = item.component
  return map
}, {})

export function categoryIconComponent(icon) {
  return categoryIconComponents[icon] || MoreFilled
}
