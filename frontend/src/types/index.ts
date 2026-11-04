export type Filters={q:string;risk:string;start:string;end:string;min_amount:string;max_amount:string};
export type Transaction={id:string;customer_id:string;timestamp:string;amount:number;city:string;state:string;category:string;kind:string;channel:string;score:number;revision:number;rule_score?:number;risk:string;status:string;reasons:string[];recommendation:string;note?:string;history?:{timestamp:string;status:string;note:string}[];model_score?:number};
export type Point={name:string;value:number};
export type Dashboard={total:number;flagged:number;rate:number;exposure:number;volume:number;mean:number;median:number;p95:number;timeline:{date:string;total:number;alerts:number}[];risks:Point[];reasons:Point[];categories:Point[];histogram:Point[];previous:Dashboard};
export type Model={name:string;precision:number;recall:number;f1:number;pr_auc:number;matrix:number[][];importance:Record<string,number>;train_size:number;test_size:number};
