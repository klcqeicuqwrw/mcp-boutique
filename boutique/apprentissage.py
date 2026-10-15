"""Petits modèles déterministes en Python standard, sans dépendance native.

Ridge : moindres carrés avec pénalité L2, intercept non pénalisé.
Logistique : maximum de vraisemblance pénalisé L2, méthode de Newton avec
recherche de pas. Préparation des variables apprise uniquement sur le train.
"""
import math
from statistics import median


def produit(a,b):
    return math.fsum(x*y for x,y in zip(a,b))


def resoudre(a,b):
    """Résout un système symétrique défini positif par Cholesky."""
    n=len(b)
    l=[[0.0]*n for _ in range(n)]
    for i in range(n):
        for j in range(i+1):
            v=a[i][j]-math.fsum(l[i][k]*l[j][k] for k in range(j))
            if i==j:
                if v<=0 or not math.isfinite(v):
                    raise ValueError('Système numérique non exploitable.')
                l[i][j]=math.sqrt(v)
            else:
                l[i][j]=v/l[j][j]
    y=[]
    for i in range(n):
        y.append((b[i]-produit(l[i][:i],y))/l[i][i])
    x=[0.0]*n
    for i in range(n-1,-1,-1):
        x[i]=(y[i]-math.fsum(l[j][i]*x[j] for j in range(i+1,n)))/l[i][i]
    return x


class Preparation:
    def fit(self,x):
        if not x or not x[0] or any(len(r)!=len(x[0]) for r in x):
            raise ValueError('Variables vides ou de tailles incohérentes.')
        colonnes=list(zip(*x))
        self.medianes=[median([v for v in col if v is not None]) if any(v is not None for v in col) else 0.0 for col in colonnes]
        completes=[[self.medianes[j] if v is None else float(v) for j,v in enumerate(r)] for r in x]
        self.moyennes=[math.fsum(col)/len(col) for col in zip(*completes)]
        self.ecarts=[math.sqrt(math.fsum((v-self.moyennes[j])**2 for v in col)/len(col)) or 1.0 for j,col in enumerate(zip(*completes))]
        return self.transform(x)

    def transform(self,x):
        return [[((self.medianes[j] if v is None else float(v))-self.moyennes[j])/self.ecarts[j] for j,v in enumerate(r)] for r in x]


class Ridge:
    def __init__(self,alpha=10.0):
        self.alpha=alpha

    def fit(self,x,y):
        self.preparation=Preparation()
        z=self.preparation.fit(x)
        n=len(z[0])
        self.intercept=math.fsum(y)/len(y)
        a=[[math.fsum(r[i]*r[j] for r in z)+(self.alpha if i==j else 0) for j in range(n)] for i in range(n)]
        b=[math.fsum(r[i]*(v-self.intercept) for r,v in zip(z,y)) for i in range(n)]
        self.coefficients=resoudre(a,b)
        return self

    def predict(self,x):
        return [self.intercept+produit(r,self.coefficients) for r in self.preparation.transform(x)]


def sigmoid(s):
    if s>=0:
        return 1/(1+math.exp(-s))
    e=math.exp(s)
    return e/(1+e)


class Logistique:
    def fit(self,x,y):
        if len(set(y))!=2:
            raise ValueError('Deux classes sont nécessaires.')
        self.preparation=Preparation()
        z=[[1.0,*r] for r in self.preparation.fit(x)]
        k=len(z[0])
        taux=(sum(y)+1)/(len(y)+2)
        w=[math.log(taux/(1-taux))]+[0.0]*(k-1)
        def perte(poids):
            s=[produit(r,poids) for r in z]
            return math.fsum(max(v,0)-c*v+math.log1p(math.exp(-abs(v))) for v,c in zip(s,y))+.5*produit(poids[1:],poids[1:])
        self.converge=False
        for _ in range(100):
            p=[sigmoid(produit(r,w)) for r in z]
            grad=[math.fsum((v-c)*r[j] for r,v,c in zip(z,p,y))+(w[j] if j else 0) for j in range(k)]
            h=[[math.fsum(v*(1-v)*r[i]*r[j] for r,v in zip(z,p))+(1.0 if i==j and i else 0)+(1e-8 if i==j else 0) for j in range(k)] for i in range(k)]
            delta=resoudre(h,grad)
            if max(abs(v) for v in delta)<1e-7:
                self.converge=True
                break
            ancien=perte(w)
            pas=1.0
            while pas>1e-8:
                candidat=[v-pas*d for v,d in zip(w,delta)]
                if perte(candidat)<=ancien:
                    w=candidat
                    break
                pas*=.5
            else:
                break
        self.coefficients=w
        if not self.converge:
            raise ValueError('La régression logistique ne converge pas ; aucun indice publié.')
        return self

    def decision_function(self,x):
        return [produit([1.0,*r],self.coefficients) for r in self.preparation.transform(x)]

    def predict_proba(self,x):
        return [[1-sigmoid(s),sigmoid(s)] for s in self.decision_function(x)]


def aire_roc(y,scores):
    positifs=sum(y)
    negatifs=len(y)-positifs
    if not positifs or not negatifs:
        raise ValueError('AUC non définie avec une seule classe.')
    groupes={}
    for label,score in zip(y,scores):
        groupes.setdefault(score,[]).append(label)
    rangs,avant=0.0,0
    for score in sorted(groupes):
        groupe=groupes[score]
        rang_moyen=avant+(len(groupe)+1)/2
        rangs+=rang_moyen*sum(groupe)
        avant+=len(groupe)
    return (rangs-positifs*(positifs+1)/2)/(positifs*negatifs)
