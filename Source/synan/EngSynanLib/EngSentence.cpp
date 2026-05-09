#include "StdAfx.h"
#include "EngSentence.h"
#include "EngFormatCaller.h"


CSentence* NewSentenceEnglish (const CSyntaxOpt* pSyntaxOptions)
{
	return new CEngSentence(pSyntaxOptions);
};

CEngSentence::CEngSentence(const CSyntaxOpt* pSyntaxOptions)  : CSentence(pSyntaxOptions)
{

}

CEngSentence::~CEngSentence()
{

};

void CEngSentence::ReadNextFromPlmLinesLanguageSpecific()
{
};


CFormatCaller* CEngSentence::GetNewFormatCaller() const
{
    return new CEngFormatCaller(GetOpt());
};

void CEngSentence::ChooseClauseType(const  std::vector<SClauseType>& vectorTypes, CMorphVariant& V)
{
	int empty_type = -1; 

	for(int i = 0 ; i < vectorTypes.size() ; i++ )
	{
		if( !vectorTypes[i].m_Root.IsEmpty() )
		{
			int node = vectorTypes[i].m_Root.m_WordNo;
			int hom = vectorTypes[i].m_Root.m_HomonymNo;

			int iUnit = V.UnitNoByWordNo(node);
			assert (iUnit != -1);
			if( V.m_SynUnits[iUnit].m_iHomonymNum == hom )
			{
				V.m_ClauseTypeNo = i;
				return;
			}				
		}
		else
			empty_type = i;

	}
	V.m_ClauseTypeNo = empty_type;
}


bool CEngSentence::RunSyntaxInClauses(ESynRulesSet rules)
{
	try
	{
		if( m_pSyntaxOptions == NULL )
			return false;

		for(int i = 0 ; i < GetClausesCount() ; i++ )
		{
			CClause& clause = GetClause(i);
			BuildGLRGroupsInClause(clause);
		}

		return true;
	}
	catch(...)
	{
		OutputErrorString("Failed RunSyntaxInClause");
		return false;
	}
}



void CEngSentence::DeleteHomOneToThousand()
{
    for (int i = 0; i < m_Words.size(); i++) {
        for (int j = 0; j < m_Words[i].GetHomonymsCount(); j++) {
            CSynHomonym &HomF = m_Words[i].GetSynHomonym(j);
            for (int k = 0; k < m_Words[i].GetHomonymsCount(); k++) {
                CSynHomonym &HomS = m_Words[i].GetSynHomonym(k);
                if (HomF.m_lFreqHom > 0 && HomS.m_lFreqHom > 0) {
                    int iFrq = HomF.m_lFreqHom / HomS.m_lFreqHom;
                    if (iFrq >= 10) HomS.m_bDelete = true;
                }
            }
        }

        m_Words[i].DeleteMarkedHomonymsBeforeClauses();
    }
}

void CEngSentence::AddWeightForSynVariantsInClauses()
{
	for (int i = 0; i < GetClausesCount(); i++)
	{
		CClause&  pClause = GetClause(i);
		
		pClause.AddVariantWeightWithHomOneToFifty();
	}
}



EClauseType CEngSentence::GetClauseTypeByAncodePattern (const CAncodePattern& Pattern) const
{
	if (GetEngGramTab()->is_verb_form(Pattern.m_iPoses)) {
		return VERB_T;
	}
	
	return UnknownPartOfSpeech;
};



bool	CEngSentence::SetClauseBorderIfThereAreTwoPotentialPredicates(int FWrd, int LWrd)
{
	return false;
};

const CEngGramTab* CEngSentence::GetEngGramTab() const
{
	return (CEngGramTab*)GetOpt()->GetGramTab();
};

const CEngSyntaxOpt* CEngSentence::GetOpt() const
{
	return (const CEngSyntaxOpt*)m_pSyntaxOptions;
};



bool CEngSentence::BuildClauses()
{
	m_bPanicMode = IsPanicSentence();

	assert ( GetClausesCount() == 0 );

	DeleteHomOneToThousand();

	FindGraPairs();

	// BuildGLRGroupsInSentence();  -- disabled, not needed for English

	if(! BuildInitialClauses() )
	{
		return false;

	};

	RunSyntaxInClauses(AllRules);

	AssignClauseNoToWords();

	return true;
}




bool	CEngSentence::AllHomonymsArePredicates(const CSynWord& W) const
{
	for (auto& h : W.m_Homonyms)
		if (!GetEngGramTab()->is_verb_form(h.m_iPoses))
			return false;
	return !W.m_Homonyms.empty();
};



bool CEngSentence::IsInitialClauseType(EClauseType x) const
{
	return x == VERB_T;
};

bool CEngSentence::IsProfession(class CSynHomonym const &)const
{
	return false;
};

bool CEngSentence::CanBeRelativeAntecedent(class CSynHomonym const &)const
{
	return false;
};

bool CEngSentence::IsRelativSentencePronoun(int,int,int &)const 
{
	return false;
};

void CEngSentence::SolveAmbiguityUsingRuleForTwoPredicates(int,int)
{
	
};

void CEngSentence::InitHomonymLanguageSpecific(CSynHomonym& H, const CLemWord* pWord)
{

};

void CEngSentence::InitHomonymMorphInfo (CSynHomonym& H)
{
    H.InitAncodePattern( );
}



int CEngSentence::GetCountOfStrongRoots(class CClause const &,struct CMorphVariant const &)const
{
	return 0;
};

void CEngSentence::BuildSubjAndPredRelation(CMorphVariant& synVariant, long RootWordNo, EClauseType ClauseType)
{
	synVariant.ResetSubj();

	long iPred = RootWordNo;
	
	// If no root is specified, try to find the first verb-like word
	if (iPred == -1) {
		for (long i = 0; i < (long)synVariant.m_SynUnits.size(); i++) {
			const CSynUnit& U = synVariant.m_SynUnits[i];
			if (U.m_Type != EWord) continue;
			const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
			const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];
			if (GetEngGramTab()->is_verb_form(H.m_iPoses) || H.HasPos(eVERB) || H.HasPos(eVBE) || H.HasPos(eMOD)) {
				iPred = i;
				break;
			}
		}
	}

	if (iPred == -1) {
		return;
	}

	synVariant.m_iPredk = iPred;

	// Basic English heuristic: the subject is often the closest Noun or Pronoun before the predicate.
	for (long i = iPred - 1; i >= 0; i--) {
		const CSynUnit& U = synVariant.m_SynUnits[i];
		if (U.m_Type != EWord) continue;

		const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
		const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

		if (GetEngGramTab()->IsMorphNoun(H.m_iPoses) || 
		    GetEngGramTab()->is_morph_pronoun(H.m_iPoses) || 
		    H.HasPos(eNOUN) || H.HasPos(ePRON) || H.HasPos(ePN)) {
			
			const CSynUnit& PU = synVariant.m_SynUnits[iPred];
			const CSynWord& PW = m_Words[PU.m_SentPeriod.m_iFirstWord];
			const CSynHomonym& PH = PW.m_Homonyms[PU.m_iHomonymNum];

			if (GetEngGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
				synVariant.m_Subjects.push_back(i);
				synVariant.m_bGoodSubject = true;
				break;
			}
		}
	}
};

void CEngSentence::AfterBuildGroupsTrigger(class CClause &)
{
};


bool CEngSentence::WordSchemeEqForThesaurus(class CSynHomonym const &,class CSynPlmLine const &)const
{
	return false;
};
