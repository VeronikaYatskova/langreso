import { InfoState } from './types'
import { put } from 'redux-saga/effects'

import { AddNewWordAction } from '../../../../entities/database'

export const actionHandler = function* (state: InfoState): any {
	yield put(AddNewWordAction({ data: state }))
}
