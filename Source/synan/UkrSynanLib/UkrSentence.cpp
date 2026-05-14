#include "UkrSentence.h"
#include "UkrSyntaxOpt.h"
#include "UkrFormatCaller.h"

CUkrSentence::CUkrSentence(const CSyntaxOpt* opt) : CSentence(opt)
{
}

CUkrSentence::~CUkrSentence()
{
}

void CUkrSentence::ReadNextFromPlmLinesLanguageSpecific()
{
}

void CUkrSentence::BuildSubjAndPredRelation(CMorphVariant& synVariant, long RootWordNo, EClauseType ClauseType)
{
	// Find the index of the predicate unit
	long iPred = -1;
	for (long i = 0; i < (long)synVariant.m_SynUnits.size(); i++) {
		if (synVariant.m_SynUnits[i].m_SentPeriod.m_iFirstWord == RootWordNo) {
			iPred = i;
			break;
		}
	}

	if (iPred == -1) return;
	synVariant.m_iPredk = iPred;

	const CSynUnit& PU = synVariant.m_SynUnits[iPred];
	const CSynWord& PW = m_Words[PU.m_SentPeriod.m_iFirstWord];
	const CSynHomonym& PH = PW.m_Homonyms[PU.m_iHomonymNum];

	// Forward scan (inverted subjects)
	for (long i = iPred + 1; i < (long)synVariant.m_SynUnits.size(); i++) {
		const CSynUnit& U = synVariant.m_SynUnits[i];
		if (U.m_Type != EWord) continue;

		const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
		const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

		if (GetUkrGramTab()->IsMorphNoun(H.m_iPoses) || 
		    GetUkrGramTab()->is_morph_pronoun(H.m_iPoses)) {
			
			if (GetUkrGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
				synVariant.m_Subjects.push_back(i);
				synVariant.m_bGoodSubject = true;
				break;
			}
		}
	}

	if (!synVariant.m_bGoodSubject) {
		// Backward scan (normal SVO)
		for (long i = iPred - 1; i >= 0; i--) {
			const CSynUnit& U = synVariant.m_SynUnits[i];
			if (U.m_Type != EWord) continue;

			const CSynWord& W = m_Words[U.m_SentPeriod.m_iFirstWord];
			const CSynHomonym& H = W.m_Homonyms[U.m_iHomonymNum];

			if (GetUkrGramTab()->IsMorphNoun(H.m_iPoses) || 
			    GetUkrGramTab()->is_morph_pronoun(H.m_iPoses)) {
				
				if (GetUkrGramTab()->GleicheSubjectPredicate(H.GetGramCodes().c_str(), PH.GetGramCodes().c_str())) {
					synVariant.m_Subjects.push_back(i);
					synVariant.m_bGoodSubject = true;
					break;
				}
			}
		}
	}
}

int CUkrSentence::GetCountOfStrongRoots(const CClause& C, const CMorphVariant& synVar) const
{
	return 1;
}

bool CUkrSentence::WordSchemeEqForThesaurus(const CSynHomonym& Homonym, const CSynPlmLine& word_scheme) const
{
	return false;
}

bool CUkrSentence::RunSyntaxInClauses(ESynRulesSet type)
{
	try {
		if (m_pSyntaxOptions == NULL) return false;
		int count = GetClausesCount();
		for (int i = 0; i < count; i++) {
			BuildGLRGroupsInClause(GetClause(i));
		}
		return true;
	}
	catch (...) {
		return false;
	}
}

void CUkrSentence::AfterBuildGroupsTrigger(CClause& C)
{
}

CFormatCaller* CUkrSentence::GetNewFormatCaller() const
{
	return new CUkrFormatCaller(GetOpt());
}

bool CUkrSentence::BuildClauses()
{
	m_bPanicMode = IsPanicSentence();
	assert(GetClausesCount() == 0);
	FindGraPairs();

	if (!BuildInitialClauses()) {
		return false;
	}

	RunSyntaxInClauses(AllRules);
	AssignClauseNoToWords();
	return true;
}

void CUkrSentence::InitHomonymMorphInfo(CSynHomonym& H)
{
	H.InitAncodePattern();
}

void CUkrSentence::InitHomonymLanguageSpecific(CSynHomonym& H, const CLemWord* pWord)
{
}

void CUkrSentence::SolveAmbiguityUsingRuleForTwoPredicates(int iFirstWord, int iLastWord)
{
}

void CUkrSentence::ChooseClauseType(const std::vector<SClauseType>& vectorTypes, CMorphVariant& V)
{
	V.m_ClauseTypeNo = 0;
}

bool CUkrSentence::SetClauseBorderIfThereAreTwoPotentialPredicates(int FWrd, int LWrd)
{
	return false;
}

bool CUkrSentence::IsInitialClauseType(EClauseType ClauseType) const
{
	return true;
}

bool CUkrSentence::IsRelativSentencePronoun(int ClauseStartWordNo, int WordNo, int& HomonymNo) const
{
	return false;
}

bool CUkrSentence::AllHomonymsArePredicates(const CSynWord& W) const
{
	for (size_t i = 0; i < W.m_Homonyms.size(); i++) {
		if (!GetUkrGramTab()->is_verb_form(W.m_Homonyms[i].m_iPoses))
			return false;
	}
	return !W.m_Homonyms.empty();
}

bool CUkrSentence::CanBeRelativeAntecedent(const CSynHomonym& H) const
{
	return GetUkrGramTab()->IsMorphNoun(H.m_iPoses);
}

bool CUkrSentence::IsProfession(const CSynHomonym& H) const
{
	return false;
}

EClauseType CUkrSentence::GetClauseTypeByAncodePattern(const CAncodePattern& Pattern) const
{
	return (EClauseType)0;
}
