import {Component,type ReactNode} from 'react';
export class ErrorBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};
 static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<main className="error-fallback"><h1>Não foi possível exibir esta tela</h1><p>Seus dados salvos continuam no banco local. Atualize a página para tentar novamente.</p><button className="primary" onClick={()=>window.location.reload()}>Atualizar página</button></main>:this.props.children}
}
